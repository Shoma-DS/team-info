#!/usr/bin/env python3
"""
fetch_materials: 人物ごとの候補画像を検索・取得して materials/ に配置するスクリプト。

改善版フロー:
  1. Wikipedia / Wikidata / Wikimedia Commons / Openverse から候補を集める
  2. 人物ごとのサブフォルダ（materials/人物名/）に複数枚ダウンロードする
  3. person_dir/metadata.json に出典メタデータを保存する
  4. OpenCV 顔検出で本人らしい画像を選別し、スロットへ配置する

Usage:
  python3 fetch_materials.py --materials-dir [絶対パス] --names "名前1,名前2,名前3"
  python3 fetch_materials.py --materials-dir [絶対パス] --script [script.md の絶対パス]
"""
import argparse
import json
import re
import shutil
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_repo_root

PROJECT_ROOT = get_repo_root()

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
USER_AGENT = "viral-template-generator/1.1"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
NON_IMAGE_EXTENSIONS = {".pdf", ".svg", ".svgz", ".mp4", ".ogv", ".webm", ".ogg"}
OPENVERSE_ALLOWED_LICENSES = {"by", "by-sa", "cc0", "pdm"}
SEARCH_SUFFIXES_ASCII = ["", " portrait", " headshot", " event", " interview", " red carpet"]
SEARCH_SUFFIXES_NON_ASCII = ["", " ポートレート", " イベント", " 会見", " インタビュー"]

SLOT_NAMES = [
    "00_hook",
    "01_opening",
    "02_s1_1", "02_s1_2", "02_s1_3",
    "03_s2_1", "03_s2_2", "03_s2_3",
    "04_s3_1", "04_s3_2", "04_s3_3",
    "99_cta",
]

# スロットごとの人物インデックス（None = CTA背景）
SLOT_CONFIG = {
    "00_hook": {"person_idx": 0},
    "01_opening": {"person_idx": 0},
    "02_s1_1": {"person_idx": 0},
    "02_s1_2": {"person_idx": 0},
    "02_s1_3": {"person_idx": 0},
    "03_s2_1": {"person_idx": 1},
    "03_s2_2": {"person_idx": 1},
    "03_s2_3": {"person_idx": 1},
    "04_s3_1": {"person_idx": 2},
    "04_s3_2": {"person_idx": 2},
    "04_s3_3": {"person_idx": 2},
    "99_cta": {"person_idx": None},
}


@dataclass(frozen=True)
class CandidateImage:
    url: str
    license: str
    source: str
    title: str = ""
    query: str = ""
    creator: str = ""
    source_url: str = ""
    provider: str = ""


@dataclass
class PersonSearchPlan:
    canonical_name: str
    aliases: list[str]
    commons_queries: list[str]
    commons_categories: list[str]
    depicts_queries: list[str]
    openverse_queries: list[str]
    seed_candidates: list[CandidateImage]
    wikidata_id: str | None = None


# ─── 汎用ユーティリティ ────────────────────────────────────────────────────

def api_get(url: str, params: dict, timeout: int = 15, retries: int = 3) -> dict:
    query = urllib.parse.urlencode(params)
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(f"{url}?{query}", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(0.7 * (attempt + 1))
    raise RuntimeError(f"API request failed: {url}?{query}") from last_error


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = re.sub(r"\s+", " ", value or "").strip()
        if not normalized or normalized in seen:
            continue
        result.append(normalized)
        seen.add(normalized)
    return result


def commons_file_url(filename: str) -> str:
    safe_name = filename.removeprefix("File:").replace(" ", "_")
    return f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(safe_name)}"


def normalize_commons_category(category_name: str) -> str:
    normalized = (category_name or "").strip().replace("_", " ")
    return normalized.removeprefix("Category:").strip()


def is_allowed_license(license_str: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", " ", (license_str or "").lower()).strip()
    if not normalized:
        return False
    if "public domain" in normalized or normalized == "pdm" or "cc0" in normalized:
        return True
    if normalized.startswith("cc by"):
        tokens = set(normalized.split())
        if "nc" in tokens or "nd" in tokens:
            return False
        return True
    return False


def is_allowed_openverse_license(license_slug: str, license_type: str) -> bool:
    slug = (license_slug or "").lower().strip()
    lic_type = (license_type or "").lower().strip()
    return slug in OPENVERSE_ALLOWED_LICENSES or "public domain" in lic_type


def get_extension_from_url(url: str) -> str:
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return ext if ext in ALLOWED_EXTENSIONS else ".jpg"


def count_image_files(directory: Path) -> int:
    return sum(1 for path in directory.iterdir() if path.is_file() and path.suffix.lower() in ALLOWED_EXTENSIONS)


# ─── Wikimedia / Wikipedia / Wikidata / Openverse ───────────────────────────

def get_image_url(filename: str) -> tuple[str | None, str | None]:
    try:
        params = {
            "action": "query",
            "titles": f"File:{filename.removeprefix('File:')}",
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "format": "json",
        }
        data = api_get(COMMONS_API, params)
    except Exception as e:
        print(f"    Commons画像情報の取得失敗: {filename} ({e})")
        return None, None

    for page in data.get("query", {}).get("pages", {}).values():
        image_info = page.get("imageinfo", [])
        if not image_info:
            continue
        meta = image_info[0].get("extmetadata", {})
        license_text = (
            meta.get("LicenseShortName", {}).get("value", "")
            + " "
            + meta.get("License", {}).get("value", "")
        ).strip()
        url = image_info[0].get("url")
        if url and is_allowed_license(license_text):
            return url, license_text
    return None, None


def search_commons(query: str, limit: int = 10) -> list[str]:
    try:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": "6",
            "srlimit": limit,
            "format": "json",
        }
        data = api_get(COMMONS_API, params)
    except Exception as e:
        print(f"    Commons検索に失敗: {query} ({e})")
        return []
    return [result["title"].removeprefix("File:") for result in data.get("query", {}).get("search", [])]


def search_commons_category(category_name: str, limit: int = 10) -> list[str]:
    normalized = normalize_commons_category(category_name)
    if not normalized:
        return []
    try:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{normalized}",
            "cmnamespace": "6",
            "cmlimit": limit,
            "format": "json",
        }
        data = api_get(COMMONS_API, params)
    except Exception as e:
        print(f"    Commonsカテゴリ取得に失敗: {normalized} ({e})")
        return []
    return [
        result["title"].removeprefix("File:")
        for result in data.get("query", {}).get("categorymembers", [])
        if result.get("title", "").startswith("File:")
    ]


def get_wikipedia_page_context(name_ja: str) -> dict:
    try:
        params = {
            "action": "query",
            "titles": name_ja,
            "redirects": 1,
            "prop": "pageprops|pageimages|langlinks",
            "ppprop": "wikibase_item",
            "piprop": "original",
            "lllang": "en",
            "lllimit": 10,
            "format": "json",
        }
        data = api_get(WIKIPEDIA_API, params)
    except Exception as e:
        print(f"    Wikipediaページ情報の取得失敗: {name_ja} ({e})")
        return {}

    for page in data.get("query", {}).get("pages", {}).values():
        if "missing" in page:
            continue

        context = {
            "ja_title": page.get("title"),
            "wikidata_id": page.get("pageprops", {}).get("wikibase_item"),
            "en_title": None,
            "seed_candidates": [],
        }
        for link in page.get("langlinks", []):
            if link.get("lang") == "en":
                context["en_title"] = link.get("*") or link.get("title")
                break

        original_url = page.get("original", {}).get("source")
        if original_url:
            filename = urllib.parse.unquote(urllib.parse.urlparse(original_url).path.split("/")[-1])
            url, license_text = get_image_url(filename)
            if url:
                context["seed_candidates"].append(
                    CandidateImage(
                        url=url,
                        license=license_text or "",
                        source="wikipedia",
                        title=page.get("title") or name_ja,
                        query=name_ja,
                        source_url=f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(page.get('title') or name_ja)}",
                    )
                )
        return context
    return {}


def get_wikidata_context(wikidata_id: str) -> dict:
    try:
        params = {
            "action": "wbgetentities",
            "ids": wikidata_id,
            "props": "labels|aliases|claims|sitelinks",
            "languages": "ja|en",
            "format": "json",
        }
        data = api_get(WIKIDATA_API, params)
    except Exception as e:
        print(f"    Wikidata情報の取得失敗: {wikidata_id} ({e})")
        return {}

    entity = data.get("entities", {}).get(wikidata_id, {})
    aliases: list[str] = []
    commons_categories: list[str] = []
    labels = entity.get("labels", {})
    for lang in ("ja", "en"):
        value = labels.get(lang, {}).get("value")
        if value:
            aliases.append(value)
        aliases.extend(alias.get("value", "") for alias in entity.get("aliases", {}).get(lang, []))

    sitelinks = entity.get("sitelinks", {})
    en_title = sitelinks.get("enwiki", {}).get("title")
    if en_title:
        aliases.append(en_title)
    commons_title = sitelinks.get("commonswiki", {}).get("title")
    if commons_title and commons_title.startswith("Category:"):
        commons_categories.append(normalize_commons_category(commons_title))

    for claim in entity.get("claims", {}).get("P373", []):
        category_value = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(category_value, str):
            commons_categories.append(normalize_commons_category(category_value))

    seed_candidates: list[CandidateImage] = []
    for claim in entity.get("claims", {}).get("P18", [])[:3]:
        filename = claim.get("mainsnak", {}).get("datavalue", {}).get("value")
        if not filename:
            continue
        url, license_text = get_image_url(filename)
        if url:
            seed_candidates.append(
                CandidateImage(
                    url=url,
                    license=license_text or "",
                    source="wikidata",
                    title=filename,
                    query=wikidata_id,
                    source_url=commons_file_url(filename),
                )
            )

    return {
        "aliases": unique_strings(aliases),
        "commons_categories": unique_strings(commons_categories),
        "seed_candidates": seed_candidates,
    }


def search_openverse(query: str, limit: int = 10) -> list[CandidateImage]:
    try:
        params = {
            "q": query,
            "page_size": limit,
        }
        data = api_get(OPENVERSE_API, params)
    except Exception as e:
        print(f"    Openverse検索に失敗: {query} ({e})")
        return []

    candidates: list[CandidateImage] = []
    for item in data.get("results", []):
        url = item.get("url")
        if not url:
            continue
        if Path(urllib.parse.urlparse(url).path).suffix.lower() in NON_IMAGE_EXTENSIONS:
            continue
        license_slug = str(item.get("license") or "").lower()
        license_version = str(item.get("license_version") or "").strip()
        license_type = str(item.get("license_type") or "").lower().strip()
        if not is_allowed_openverse_license(license_slug, license_type):
            continue
        license_text = " ".join(part for part in [license_slug, license_version, license_type] if part)
        candidates.append(
            CandidateImage(
                url=url,
                license=license_text,
                source="openverse",
                title=str(item.get("title") or ""),
                query=query,
                creator=str(item.get("creator") or ""),
                source_url=str(item.get("foreign_landing_url") or ""),
                provider=str(item.get("provider") or item.get("source") or ""),
            )
        )
    return candidates


# ─── ダウンロード補助 ─────────────────────────────────────────────────────

def is_image_url(url: str) -> bool:
    """URL が画像ファイル（jpg/png/webp）かどうか確認する。PDFや動画は除外。"""
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    return ext in ALLOWED_EXTENSIONS or ext == ""


def download_image(url: str, dest_path: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = (resp.headers.get("Content-Type") or "").lower()
            if any(token in content_type for token in ("pdf", "video", "audio", "svg")):
                print(f"    スキップ（非画像: {content_type}）")
                return False
            data = resp.read()
        dest_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"    ダウンロード失敗: {e}")
        return False


def save_person_metadata(
    person_dir: Path,
    plan: PersonSearchPlan,
    downloaded_records: list[dict],
    total_candidates: int,
) -> None:
    metadata = {
        "canonical_name": plan.canonical_name,
        "wikidata_id": plan.wikidata_id,
        "aliases": plan.aliases,
        "commons_queries": plan.commons_queries,
        "commons_categories": plan.commons_categories,
        "depicts_queries": plan.depicts_queries,
        "openverse_queries": plan.openverse_queries,
        "downloaded_count": len(downloaded_records),
        "candidate_pool_count": total_candidates,
        "downloaded": downloaded_records,
    }
    (person_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ─── 顔検出 ───────────────────────────────────────────────────────────────

def has_face(image_path: Path) -> bool | None:
    """
    OpenCV Haar Cascade で顔を検出。
    戻り値: True=顔あり / False=顔なし / None=検出不能（cv2なし等）
    """
    try:
        import cv2

        img = cv2.imread(str(image_path))
        if img is None:
            return False
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        detector = cv2.CascadeClassifier(cascade_path)
        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        return len(faces) > 0
    except Exception:
        return None


# ─── 人物ごと候補ダウンロード ─────────────────────────────────────────────

def build_commons_queries(aliases: list[str]) -> list[str]:
    queries: list[str] = []
    for alias in aliases[:6]:
        suffixes = SEARCH_SUFFIXES_ASCII if alias.isascii() else SEARCH_SUFFIXES_NON_ASCII
        for suffix in suffixes:
            queries.append(f"{alias}{suffix}")
    return unique_strings(queries)[:18]


def build_openverse_queries(aliases: list[str]) -> list[str]:
    ascii_aliases = [alias for alias in aliases if alias.isascii()]
    prioritized = ascii_aliases + [alias for alias in aliases if alias not in ascii_aliases]
    queries: list[str] = []
    for alias in prioritized[:6]:
        suffixes = SEARCH_SUFFIXES_ASCII if alias.isascii() else [""]
        for suffix in suffixes:
            queries.append(f"{alias}{suffix}")
    return unique_strings(queries)[:18]


def build_person_search_plan(name: str) -> PersonSearchPlan:
    aliases = [name]
    commons_categories: list[str] = []
    seed_candidates: list[CandidateImage] = []
    wikidata_id: str | None = None

    wiki_context = get_wikipedia_page_context(name)
    if wiki_context:
        wikidata_id = wiki_context.get("wikidata_id")
        aliases.extend([wiki_context.get("ja_title") or "", wiki_context.get("en_title") or ""])
        seed_candidates.extend(wiki_context.get("seed_candidates", []))

    if wikidata_id:
        wikidata_context = get_wikidata_context(wikidata_id)
        aliases.extend(wikidata_context.get("aliases", []))
        commons_categories.extend(wikidata_context.get("commons_categories", []))
        seed_candidates.extend(wikidata_context.get("seed_candidates", []))

    alias_list = unique_strings(aliases)
    category_list = unique_strings(commons_categories)
    return PersonSearchPlan(
        canonical_name=name,
        aliases=alias_list,
        commons_queries=build_commons_queries(alias_list),
        commons_categories=category_list,
        depicts_queries=[f"haswbstatement:P180={wikidata_id}"] if wikidata_id else [],
        openverse_queries=build_openverse_queries(alias_list),
        seed_candidates=seed_candidates,
        wikidata_id=wikidata_id,
    )


def fetch_candidates_for_person(name: str, person_dir: Path, n_candidates: int = 10) -> list[Path]:
    """
    1人分の候補画像を person_dir にダウンロードする。
    戻り値: ダウンロードできたファイルのリスト
    """
    person_dir.mkdir(parents=True, exist_ok=True)
    print(f"\n  [{name}] 候補画像を検索・取得中... （目標: {n_candidates}枚）")

    plan = build_person_search_plan(name)
    candidate_pool: list[CandidateImage] = []
    used_urls: set[str] = set()
    target_pool_size = max(n_candidates * 4, 16)

    def add_candidate(candidate: CandidateImage) -> bool:
        if not candidate.url or candidate.url in used_urls:
            return False
        if not is_image_url(candidate.url):
            return False
        ext = Path(urllib.parse.urlparse(candidate.url).path).suffix.lower()
        if ext in NON_IMAGE_EXTENSIONS:
            return False
        candidate_pool.append(candidate)
        used_urls.add(candidate.url)
        return True

    for candidate in plan.seed_candidates:
        add_candidate(candidate)

    for category_name in plan.commons_categories:
        if len(candidate_pool) >= target_pool_size:
            break
        for filename in search_commons_category(category_name, limit=16):
            url, license_text = get_image_url(filename)
            if not url:
                continue
            add_candidate(
                CandidateImage(
                    url=url,
                    license=license_text or "",
                    source="commons_category",
                    title=filename,
                    query=category_name,
                    source_url=commons_file_url(filename),
                )
            )
            if len(candidate_pool) >= target_pool_size:
                break

    for query in plan.depicts_queries:
        if len(candidate_pool) >= target_pool_size:
            break
        for filename in search_commons(query, limit=16):
            url, license_text = get_image_url(filename)
            if not url:
                continue
            add_candidate(
                CandidateImage(
                    url=url,
                    license=license_text or "",
                    source="commons_depicts",
                    title=filename,
                    query=query,
                    source_url=commons_file_url(filename),
                )
            )
            if len(candidate_pool) >= target_pool_size:
                break

    for query in plan.commons_queries:
        if len(candidate_pool) >= target_pool_size:
            break
        for filename in search_commons(query, limit=12):
            url, license_text = get_image_url(filename)
            if not url:
                continue
            add_candidate(
                CandidateImage(
                    url=url,
                    license=license_text or "",
                    source="commons",
                    title=filename,
                    query=query,
                    source_url=commons_file_url(filename),
                )
            )
            if len(candidate_pool) >= target_pool_size:
                break

    for query in plan.openverse_queries:
        if len(candidate_pool) >= target_pool_size:
            break
        for candidate in search_openverse(query, limit=12):
            add_candidate(candidate)
            if len(candidate_pool) >= target_pool_size:
                break

    source_counts: dict[str, int] = {}
    for candidate in candidate_pool:
        source_counts[candidate.source] = source_counts.get(candidate.source, 0) + 1

    if plan.aliases:
        alias_preview = ", ".join(plan.aliases[:5])
        print(f"  → 検索名: {alias_preview}")
    if plan.commons_categories:
        print(f"  → Commonsカテゴリ: {', '.join(plan.commons_categories[:3])}")
    if plan.depicts_queries:
        print(f"  → Structured search: {', '.join(plan.depicts_queries)}")
    if source_counts:
        source_summary = ", ".join(f"{source}={count}" for source, count in sorted(source_counts.items()))
        print(f"  → 候補内訳: {source_summary}")
    print(f"  → {len(candidate_pool)} 件の候補URL を取得")

    downloaded: list[Path] = []
    downloaded_records: list[dict] = []
    total_to_download = min(len(candidate_pool), n_candidates)
    for i, candidate in enumerate(candidate_pool[:n_candidates]):
        dest = person_dir / f"{i + 1:02d}{get_extension_from_url(candidate.url)}"
        print(f"  → {i + 1}/{total_to_download} ダウンロード中... [{candidate.source}]")
        if download_image(candidate.url, dest):
            downloaded.append(dest)
            record = asdict(candidate)
            record["local_path"] = dest.name
            downloaded_records.append(record)

    save_person_metadata(person_dir, plan, downloaded_records, len(candidate_pool))
    print(f"  → ダウンロード完了: {len(downloaded)} 枚")
    return downloaded


# ─── 顔検出フィルタ & スロット選別 ───────────────────────────────────────

def select_images_by_face(downloaded: list[Path], n_needed: int) -> tuple[list[Path], list[str]]:
    """
    顔検出でフィルタし n_needed 枚を選ぶ。
    顔が検出されなかった画像（face_ng）はディスクから削除する。
    戻り値: (selected: list[Path], status: list[str])
      status は "ok" | "unverified"
    """
    face_ok, face_ng, face_unknown = [], [], []
    for image_path in downloaded:
        result = has_face(image_path)
        if result is True:
            face_ok.append(image_path)
        elif result is False:
            face_ng.append(image_path)
        else:
            face_unknown.append(image_path)

    # 顔なし画像をディスクから削除
    deleted_count = 0
    for image_path in face_ng:
        try:
            image_path.unlink()
            deleted_count += 1
        except Exception as e:
            print(f"    削除失敗: {image_path.name} ({e})")

    print(
        f"    顔検出: ✅ {len(face_ok)}枚 / ❓ {len(face_unknown)}枚（検出不能）/ "
        f"🗑 {deleted_count}枚（顔なし→削除）"
    )

    selected: list[Path] = []
    status: list[str] = []

    for image_path in face_ok[:n_needed]:
        selected.append(image_path)
        status.append("ok")

    if len(selected) < n_needed:
        for image_path in face_unknown[: n_needed - len(selected)]:
            selected.append(image_path)
            status.append("unverified")

    return selected, status


# ─── script.md パース ─────────────────────────────────────────────────────

def parse_script(script_path: Path) -> dict:
    text = script_path.read_text(encoding="utf-8")
    result: dict = {"hook": "", "sections": []}
    hook_match = re.search(r"##\s*フック.*?\n+(.*?)(?=\n---|\Z)", text, re.DOTALL)
    if hook_match:
        result["hook"] = hook_match.group(1).strip()
    for label, body in re.findall(
        r"##\s*本編\s*セクション\d+[:：]\s*([^\n]+)\n+(.*?)(?=\n---|\Z)",
        text,
        re.DOTALL,
    ):
        result["sections"].append({"label": label.strip(), "text": body.strip()})
    return result


def extract_names_from_section(section_text: str) -> list[str]:
    names = re.findall(r"「([^」]{2,10})」", section_text)
    if not names:
        names = re.findall(
            r"^\s*([ァ-ヶーa-zA-Z\u4e00-\u9fff]{2,8})\s*$",
            section_text,
            re.MULTILINE,
        )
    return list(dict.fromkeys(names))


# ─── メイン ───────────────────────────────────────────────────────────────

def run(
    materials_dir: Path,
    names: list[str],
    script_path: Path | None,
    candidates_per_person: int = 10,
    composition_id: str = "",
):
    materials_dir.mkdir(parents=True, exist_ok=True)

    # コンポジションIDフォルダ: materials/{composition_id}/ にまとめる
    candidate_base = materials_dir / composition_id if composition_id else materials_dir
    candidate_base.mkdir(parents=True, exist_ok=True)

    if script_path and script_path.exists() and not names:
        parsed = parse_script(script_path)
        for section in parsed.get("sections", []):
            names += extract_names_from_section(section["text"])
        print(f"script.md から検出した人物名: {names}")

    if not names:
        print("人物名が指定されていません。--names または --script を指定してください。")
        sys.exit(1)

    print(f"\n取得対象: {names}")
    print(f"候補画像の保管先: {candidate_base}")
    print(f"スロット配置先: {materials_dir}")

    # ─── Step 1: 人物ごとサブフォルダに候補をダウンロード ───────────────
    print("\n" + "=" * 60)
    print("Step 1: 人物ごとに候補画像を取得")
    print("=" * 60)

    # hook 用フォルダを事前作成
    hook_dir = candidate_base / "hook"
    hook_dir.mkdir(exist_ok=True)
    print(f"  [hook] フォルダ準備: {hook_dir}")

    person_candidates: dict[str, list[Path]] = {}
    for name in names:
        person_dir = candidate_base / name
        person_candidates[name] = fetch_candidates_for_person(
            name,
            person_dir,
            n_candidates=candidates_per_person,
        )

    # CTA 背景
    cta_dir = candidate_base / "_cta"
    cta_dir.mkdir(exist_ok=True)
    print("\n  [CTA背景] 検索中...")
    cta_file: Path | None = None
    for filename in search_commons("stage spotlight dark background", limit=5):
        url, license_text = get_image_url(filename)
        if not url:
            continue
        dest = cta_dir / f"01{get_extension_from_url(url)}"
        if download_image(url, dest):
            cta_file = dest
            print(f"  → CTA背景を取得: {dest.name}")
            break
    if not cta_file:
        print("  → CTA背景の自動取得に失敗しました（手動配置が必要）")

    # ─── Step 2: 顔検出でフィルタ → スロットへ配置 ──────────────────────
    print("\n" + "=" * 60)
    print("Step 2: 顔検出フィルタ → スロットへ配置")
    print("=" * 60)

    person_slot_count: dict[str, int] = {name: 0 for name in names}
    for config in SLOT_CONFIG.values():
        idx = config["person_idx"]
        if idx is not None and idx < len(names):
            person_slot_count[names[idx]] += 1

    selected_per_person: dict[str, list[Path]] = {}
    status_per_person: dict[str, list[str]] = {}
    for name in names:
        needed = person_slot_count[name]
        print(f"\n  [{name}] 顔検出フィルタ中... （必要: {needed}枚）")
        selected, status = select_images_by_face(person_candidates[name], needed)
        selected_per_person[name] = selected
        status_per_person[name] = status
        print(f"  → 選別結果: {len(selected)}/{needed} 枚")

    success: list[str] = []
    failed: list[tuple[str, str]] = []
    needs_review: list[tuple[str, str, Path, str]] = []
    person_slot_idx: dict[str, int] = {name: 0 for name in names}

    for slot in SLOT_NAMES:
        idx = SLOT_CONFIG[slot]["person_idx"]

        if idx is None:
            if cta_file:
                dest = materials_dir / f"{slot}{cta_file.suffix}"
                shutil.copy2(cta_file, dest)
                success.append(slot)
            else:
                failed.append((slot, "CTA背景"))
            continue

        if idx >= len(names):
            failed.append((slot, f"人物{idx + 1}（未指定）"))
            continue

        name = names[idx]
        selected = selected_per_person.get(name, [])
        statuses = status_per_person.get(name, [])
        slot_index = person_slot_idx[name]

        if slot_index < len(selected):
            src = selected[slot_index]
            dest = materials_dir / f"{slot}{src.suffix}"
            shutil.copy2(src, dest)
            status = statuses[slot_index] if slot_index < len(statuses) else "unverified"
            if status == "ok":
                success.append(slot)
            else:
                needs_review.append((slot, name, dest, status))
            person_slot_idx[name] += 1
        else:
            failed.append((slot, name))

    # ─── Step 3: 結果レポート ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("取得結果レポート")
    print("=" * 60)
    print(f"✅ 顔検出OK・自動配置: {len(success)} スロット")

    if needs_review:
        print(f"\n⚠  要確認（顔検出が不確か）: {len(needs_review)} 件")
        print("  以下のスロットは画像が本人かどうか目視で確認してください。")
        for slot, name, path, status in needs_review:
            label = "検出不能（cv2未対応）"
            print(f"  {slot:12s} ← [{name}] {path.name}  ({label})")

    if failed:
        print(f"\n❌ 取得失敗（手動配置が必要）: {len(failed)} 件")
        for slot, name in failed:
            print(f"  {slot}.jpg  ← 「{name}」の画像を手動で配置してください")
            print(f"    配置先: {materials_dir / slot}.jpg")
        print("\n  推奨サイト: Wikimedia Commons / Openverse / Pexels / Unsplash")

    print("\n人物別サブフォルダ（候補画像の保管場所）:")
    print(f"  hook/  → {hook_dir}")
    for name in names:
        person_dir = candidate_base / name
        count = count_image_files(person_dir) if person_dir.exists() else 0
        print(f"  {person_dir}  ({count}枚 + metadata.json)")

    print("\n⚠  ライセンス: CC 画像はクレジット表記が必要な場合があります。")
    print("⚠  Openverse のライセンス情報は出典側で要再確認です。")
    print("⚠  肖像権: 日本の芸能人画像は別途権利確認が必要です。")
    print("次の手順: 不足分を手動配置し、素材が揃ったら upscale_materials.py で一括補正してください。")
    print("=" * 60)


# ─── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Wikipedia / Wikidata / Commons / Openverse から素材画像を取得"
    )
    parser.add_argument("--materials-dir", type=Path)
    parser.add_argument("--names", type=str, default="")
    parser.add_argument("--script", type=Path)
    parser.add_argument("--output-title", type=str, default="")
    parser.add_argument("--composition-id", type=str, default="", help="コンポジションID（日本語）。materials直下にこの名前のフォルダを作成する。")
    parser.add_argument("--candidates-per-person", type=int, default=10)
    args = parser.parse_args()

    if args.materials_dir:
        materials_dir = args.materials_dir
    elif args.output_title:
        materials_dir = (
            PROJECT_ROOT / "inputs" / "viral-analysis" / "output" / args.output_title / "materials"
        )
    else:
        print("materials フォルダのパスを入力してください:")
        materials_dir = Path(input("> ").strip())

    names = [name.strip() for name in args.names.split(",") if name.strip()] if args.names else []
    run(
        materials_dir,
        names,
        args.script,
        candidates_per_person=max(args.candidates_per_person, 1),
        composition_id=args.composition_id,
    )


if __name__ == "__main__":
    main()
