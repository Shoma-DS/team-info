#!/usr/bin/env python3
"""
fetch_materials: Wikimedia Commons API から CC/PD ライセンス画像を取得して
materials/ フォルダに配置するスクリプト。

Usage:
  python3 fetch_materials.py --materials-dir [絶対パス] --names "名前1,名前2,名前3"
  python3 fetch_materials.py --materials-dir [絶対パス] --script [script.md の絶対パス]
  python3 fetch_materials.py  # インタラクティブモード
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

COMMON_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "common" / "scripts"
if str(COMMON_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_SCRIPTS_DIR))

from runtime_common import get_repo_root

PROJECT_ROOT = get_repo_root()

# ─── Wikimedia Commons API ──────────────────────────────────────────────────
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API = "https://ja.wikipedia.org/w/api.php"

# 許可するライセンスキーワード（商用利用可能なもの）
ALLOWED_LICENSES = [
    "cc-by", "cc-by-sa", "cc0", "pd", "public domain",
    "cc-zero", "attribution", "free",
]

# 材料フォルダの命名規則（タイムライン順）
SLOT_NAMES = [
    "00_hook",
    "01_opening",
    "02_s1_1",
    "02_s1_2",
    "02_s1_3",
    "03_s2_1",
    "03_s2_2",
    "03_s2_3",
    "04_s3_1",
    "04_s3_2",
    "04_s3_3",
    "99_cta",
]


# ─── ユーティリティ ──────────────────────────────────────────────────────────

def api_get(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    full_url = f"{url}?{query}"
    req = urllib.request.Request(full_url, headers={"User-Agent": "viral-template-generator/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def is_allowed_license(license_str: str) -> bool:
    ls = license_str.lower()
    return any(kw in ls for kw in ALLOWED_LICENSES)


def get_image_url(filename: str) -> str | None:
    """Commons のファイル名から直接ダウンロード URL を取得する"""
    params = {
        "action": "query",
        "titles": f"File:{filename}",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "format": "json",
    }
    data = api_get(COMMONS_API, params)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        ii = page.get("imageinfo", [])
        if not ii:
            continue
        meta = ii[0].get("extmetadata", {})
        license_text = (
            meta.get("LicenseShortName", {}).get("value", "")
            + " "
            + meta.get("License", {}).get("value", "")
        )
        if is_allowed_license(license_text):
            return ii[0].get("url"), license_text.strip()
        else:
            print(f"  ライセンス非対応: {license_text.strip()} → スキップ")
            return None, None
    return None, None


def search_commons(query: str, limit: int = 5) -> list[dict]:
    """Commons でファイルを検索し、候補リストを返す"""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srnamespace": "6",  # File namespace
        "srlimit": limit,
        "format": "json",
    }
    data = api_get(COMMONS_API, params)
    results = data.get("query", {}).get("search", [])
    return [r["title"].removeprefix("File:") for r in results]


def search_wikipedia_image(name_ja: str) -> tuple[str | None, str | None]:
    """
    ja.Wikipedia の人物記事からメイン画像ファイル名を取得し、
    Commons で URL を解決して返す。
    戻り値: (download_url, license_str) or (None, None)
    """
    # Wikipedia で記事を検索
    params = {
        "action": "query",
        "titles": name_ja,
        "prop": "pageimages",
        "piprop": "original",
        "format": "json",
    }
    data = api_get(WIKIPEDIA_API, params)
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        original = page.get("original", {})
        if original:
            # Wikipedia の画像は Commons 経由
            img_url = original.get("source")
            if img_url:
                # ライセンス確認のためファイル名を抽出して Commons に問い合わせ
                filename = urllib.parse.unquote(img_url.split("/")[-1])
                url, lic = get_image_url(filename)
                if url:
                    return url, lic
    return None, None


def download_image(url: str, dest_path: Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "viral-template-generator/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest_path.write_bytes(resp.read())
        return True
    except Exception as e:
        print(f"  ダウンロード失敗: {e}")
        return False


# ─── script.md からセクション名・人物名を抽出 ─────────────────────────────

def parse_script(script_path: Path) -> dict:
    """
    script.md を解析して、セクションごとのキーワード・人物名を返す。
    戻り値例:
    {
        "hook": "食べちまった芸能人3選",
        "sections": [
            {"label": "セクション1", "text": "..."},
            ...
        ]
    }
    """
    text = script_path.read_text(encoding="utf-8")
    result = {"hook": "", "sections": []}

    hook_match = re.search(r"##\s*フック.*?\n+(.*?)(?=\n---|\Z)", text, re.DOTALL)
    if hook_match:
        result["hook"] = hook_match.group(1).strip()

    section_matches = re.findall(
        r"##\s*本編\s*セクション\d+[:：]\s*([^\n]+)\n+(.*?)(?=\n---|\Z)",
        text, re.DOTALL
    )
    for label, body in section_matches:
        result["sections"].append({"label": label.strip(), "text": body.strip()})

    return result


def extract_names_from_section(section_text: str) -> list[str]:
    """セクションのテキストから人物名らしき文字列を抽出する（簡易版）"""
    # 「」で囲まれた名前 or カタカナ・漢字2〜6文字の単語
    names = re.findall(r"「([^」]{2,10})」", section_text)
    if not names:
        # 行頭の見出し的な単語（改行後に続く2〜8文字の名前）
        names = re.findall(r"^\s*([ァ-ヶーa-zA-Z\u4e00-\u9fff]{2,8})\s*$",
                           section_text, re.MULTILINE)
    return list(dict.fromkeys(names))  # 重複除去・順序保持


# ─── メイン処理 ──────────────────────────────────────────────────────────────

# スロットごとに使う検索クエリのサフィックス（同一人物で異なる画像を取得するため）
SLOT_QUERY_SUFFIXES: dict[str, str] = {
    "00_hook":    "",
    "01_opening": "",
    "02_s1_1":    "",
    "02_s1_2":    " event stage",
    "02_s1_3":    " fashion",
    "03_s2_1":    "",
    "03_s2_2":    " event stage",
    "03_s2_3":    " fashion",
    "04_s3_1":    "",
    "04_s3_2":    " event stage",
    "04_s3_3":    " fashion",
    "99_cta":     "",
}


def fetch_for_name(
    name: str,
    slot: str,
    materials_dir: Path,
    used_urls: set[str],
) -> bool:
    """
    1人分の画像を取得して materials_dir/[slot].jpg に保存する。
    used_urls に既出の URL は使わず、別の候補を探す。
    戻り値: 成功したか
    """
    suffix = SLOT_QUERY_SUFFIXES.get(slot, "")
    query = f"{name}{suffix}"
    print(f"\n  [{slot}] 「{query}」を検索中...")

    candidate_urls: list[tuple[str, str]] = []

    # 1. Wikipedia から取得を試みる（suffix なしの場合のみ）
    if not suffix:
        url, lic = search_wikipedia_image(name)
        if url and url not in used_urls:
            candidate_urls.append((url, lic or ""))

    # 2. Commons で複数候補を取得
    commons_candidates = search_commons(query, limit=10)
    for candidate in commons_candidates:
        url, lic = get_image_url(candidate)
        if url and url not in used_urls:
            candidate_urls.append((url, lic or ""))
            if len(candidate_urls) >= 3:
                break

    if not candidate_urls:
        # suffix なしで再試行
        if suffix:
            fallback_candidates = search_commons(name, limit=10)
            for candidate in fallback_candidates:
                url, lic = get_image_url(candidate)
                if url and url not in used_urls:
                    candidate_urls.append((url, lic or ""))
                    break

    if not candidate_urls:
        print(f"  → 取得できる画像が見つかりませんでした（手動で配置してください）")
        return False

    url, lic = candidate_urls[0]
    used_urls.add(url)

    ext = Path(urllib.parse.urlparse(url).path).suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    dest = materials_dir / f"{slot}{ext}"

    print(f"  → ダウンロード中: {url[:80]}...")
    if download_image(url, dest):
        print(f"  → 保存: {dest.name}  ライセンス: {lic}")
        return True
    return False


def run(materials_dir: Path, names: list[str], script_path: Path | None):
    materials_dir.mkdir(parents=True, exist_ok=True)

    # script.md がある場合は人物名を補完
    if script_path and script_path.exists() and not names:
        print(f"\nscript.md を読み込んでいます: {script_path}")
        parsed = parse_script(script_path)
        for sec in parsed.get("sections", []):
            names += extract_names_from_section(sec["text"])
        print(f"検出された人物名候補: {names}")

    if not names:
        print("人物名が指定されていません。")
        print("使い方: --names \"名前1,名前2,名前3\" または --script [script.mdパス]")
        sys.exit(1)

    print(f"\n取得対象: {names}")
    print(f"出力先: {materials_dir}")
    print(f"スロット数: {len(SLOT_NAMES)}（本編3名 × 3枚 + hook/opening/cta）")

    # スロットへのマッピング
    slot_name_map: dict[str, str] = {}
    if len(names) >= 1:
        slot_name_map["00_hook"]    = names[0]
        slot_name_map["01_opening"] = names[0]
        slot_name_map["02_s1_1"]    = names[0]
        slot_name_map["02_s1_2"]    = names[0]
        slot_name_map["02_s1_3"]    = names[0]
    if len(names) >= 2:
        slot_name_map["03_s2_1"] = names[1]
        slot_name_map["03_s2_2"] = names[1]
        slot_name_map["03_s2_3"] = names[1]
    if len(names) >= 3:
        slot_name_map["04_s3_1"] = names[2]
        slot_name_map["04_s3_2"] = names[2]
        slot_name_map["04_s3_3"] = names[2]
    slot_name_map["99_cta"] = "stage spotlight background"

    # 人物ごとに used_urls を管理して重複を防ぐ
    used_urls_per_person: dict[str, set[str]] = {}

    success, failed = [], []
    for slot in SLOT_NAMES:
        search_name = slot_name_map.get(slot)
        if not search_name:
            continue
        used_urls = used_urls_per_person.setdefault(search_name, set())
        ok = fetch_for_name(search_name, slot, materials_dir, used_urls)
        if ok:
            success.append(slot)
        else:
            failed.append((slot, search_name))

    # ─── 結果レポート ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("取得結果")
    print("=" * 60)
    print(f"成功: {len(success)} / {len(SLOT_NAMES)} スロット")
    if failed:
        print(f"\n⚠ 手動配置が必要なスロット ({len(failed)}件):")
        for slot, name in failed:
            print(f"  {slot}.jpg  ← 「{name}」の画像を手動で配置してください")
        print("\n推奨素材サイト:")
        print("  https://commons.wikimedia.org/")
        print("  https://www.pexels.com/")
        print("  https://unsplash.com/")
    else:
        print("\n全スロットの自動取得に成功しました！")

    print("\n⚠ 注意: CC ライセンス画像はクレジット表記が必要な場合があります。")
    print("  利用前に各画像のライセンスを必ず確認してください。")
    print("  また日本の肖像権については別途ご確認ください。")
    print("=" * 60)


# ─── CLI エントリポイント ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wikimedia Commons から素材画像を取得")
    parser.add_argument("--materials-dir", type=Path,
                        help="materials/ フォルダの絶対パス")
    parser.add_argument("--names", type=str, default="",
                        help="カンマ区切りの人物名（例: '石原さとみ,新垣結衣,広瀬すず'）")
    parser.add_argument("--script", type=Path,
                        help="script.md の絶対パス（自動で人物名を抽出）")
    parser.add_argument("--output-title", type=str, default="",
                        help="出力タイトルフォルダ名（--materials-dir 未指定時に使用）")
    args = parser.parse_args()

    # materials-dir の決定
    if args.materials_dir:
        materials_dir = args.materials_dir
    elif args.output_title:
        materials_dir = PROJECT_ROOT / "inputs" / "viral-analysis" / "output" / args.output_title / "materials"
    else:
        # インタラクティブモード
        print("materials フォルダのパスを入力してください:")
        materials_dir = Path(input("> ").strip())

    names = [n.strip() for n in args.names.split(",") if n.strip()] if args.names else []

    run(materials_dir, names, args.script)


if __name__ == "__main__":
    main()
