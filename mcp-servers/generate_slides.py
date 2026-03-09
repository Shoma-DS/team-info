#!/usr/bin/env python3
"""
スライド背景画像生成スクリプト

フロー:
  1. 台本を段落単位でスライドに分割
  2. 各スライドからキーワードを抽出
  3. Pixabay API で台本に合った背景画像を検索・ダウンロード
  4. outputs/slide_images/{テーマ}/ に保存
  5. manifest.json（テキスト + 画像パス）を出力 → Remotion が使用

使い方:
  python3 mcp-servers/generate_slides.py \
    --script 台本.md \
    --theme テーマ名 \
    --pixabay-key YOUR_API_KEY

Pixabay無料APIキー取得: https://pixabay.com/api/docs/
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import requests

# ===== パス設定 =====
BASE_DIR    = Path(__file__).resolve().parent.parent
SCRIPT_DIR  = BASE_DIR / "Remotion" / "scripts" / "voice_scripts"
# Remotion の public/ 直下に保存（staticFile で直接参照できる）
PUBLIC_DIR  = BASE_DIR / "Remotion" / "my-video" / "public"
OUTPUT_BASE = PUBLIC_DIR / "assets" / "slide_images"
SECRETS_DIR = Path.home() / ".secrets"
PIXABAY_KEY_FILE = SECRETS_DIR / "pixabay_api_key.txt"

PIXABAY_API = "https://pixabay.com/api/"
MAX_CHARS_PER_SLIDE = 120

# スライド枚数の上限（188枚は多すぎるので間引く）
MAX_SLIDES = 60

# 地政学・旅行・知識系コンテンツ向けのデフォルトキーワードマッピング（日→英）
KEYWORD_MAP: dict[str, str] = {
    "地政学": "geopolitics world map",
    "地理": "geography landscape",
    "海": "ocean sea",
    "山": "mountain landscape",
    "川": "river nature",
    "砂漠": "desert sand",
    "森": "forest nature",
    "都市": "city urban",
    "歴史": "history ancient",
    "文化": "culture tradition",
    "戦争": "war history",
    "平和": "peace nature calm",
    "経済": "economy finance",
    "政治": "politics government",
    "アジア": "asia landscape",
    "ヨーロッパ": "europe landscape",
    "アフリカ": "africa landscape",
    "アメリカ": "america landscape",
    "中国": "china landscape",
    "日本": "japan landscape",
    "ロシア": "russia landscape",
    "シルクロード": "silk road ancient",
    "貿易": "trade shipping",
    "石油": "oil industry",
    "エネルギー": "energy power",
    "気候": "climate weather",
    "旅": "travel journey",
    "夜": "night calm",
    "星": "stars night sky",
    "空": "sky clouds",
    "地球": "earth globe",
}


# ===== ユーティリティ =====

def load_pixabay_key(cli_key: Optional[str]) -> str:
    if cli_key:
        return cli_key
    if PIXABAY_KEY_FILE.exists():
        return PIXABAY_KEY_FILE.read_text().strip()
    print("エラー: Pixabay APIキーが見つかりません。")
    print("  --pixabay-key で指定するか、以下に保存してください:")
    print(f"  {PIXABAY_KEY_FILE}")
    print("  取得先: https://pixabay.com/api/docs/")
    sys.exit(1)

def save_pixabay_key(key: str):
    SECRETS_DIR.mkdir(exist_ok=True)
    PIXABAY_KEY_FILE.write_text(key)
    os.chmod(PIXABAY_KEY_FILE, 0o600)
    print(f"  APIキーを保存しました: {PIXABAY_KEY_FILE}")


# ===== 台本パース =====

def split_script_to_slides(script_text: str) -> list[str]:
    """台本を段落単位でスライドに分割する"""
    paragraphs = re.split(r'\n{2,}|(?=^#{1,3} )', script_text, flags=re.MULTILINE)
    slides = []
    for para in paragraphs:
        para = re.sub(r'^#{1,3}\s*', '', para.strip(), flags=re.MULTILINE)
        para = re.sub(r'\[.*?\]|\(.*?\)', '', para).strip()
        if not para:
            continue
        if len(para) <= MAX_CHARS_PER_SLIDE:
            slides.append(para)
        else:
            sentences = re.split(r'(?<=。)', para)
            current = ""
            for s in sentences:
                if current and len(current) + len(s) > MAX_CHARS_PER_SLIDE:
                    slides.append(current.strip())
                    current = s
                else:
                    current += s
            if current.strip():
                slides.append(current.strip())
    return slides


def thin_slides(slides: list[str], max_count: int) -> list[str]:
    """スライド数を間引いて上限に収める"""
    if len(slides) <= max_count:
        return slides
    step = len(slides) / max_count
    return [slides[int(i * step)] for i in range(max_count)]


# ===== キーワード抽出 =====

def extract_keywords(text: str) -> str:
    """日本語テキストから英語検索クエリを生成する"""
    # マッピングテーブルから一致するキーワードを探す
    matched = []
    for ja, en in KEYWORD_MAP.items():
        if ja in text:
            matched.append(en)
    if matched:
        return matched[0]  # 最初の一致を使用

    # カタカナ語を抽出（外来語・地名が多い）
    katakana = re.findall(r'[ァ-ヶー]{3,}', text)
    if katakana:
        # カタカナをローマ字風に変換（簡易）
        return f"landscape travel {katakana[0]}"

    # デフォルト: テーマに合わせた汎用クエリ
    return "landscape nature calm"


# ===== Pixabay 画像取得 =====

def search_pixabay(query: str, api_key: str, per_page: int = 5) -> Optional[str]:
    """Pixabay で画像を検索して最初の URL を返す"""
    try:
        resp = requests.get(
            PIXABAY_API,
            params={
                "key": api_key,
                "q": query,
                "image_type": "photo",
                "orientation": "horizontal",
                "safesearch": "true",
                "per_page": per_page,
                "min_width": 1920,
            },
            timeout=10,
        )
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        if hits:
            return hits[0].get("largeImageURL") or hits[0].get("webformatURL")
    except Exception as e:
        print(f"    [警告] Pixabay検索失敗 ({query}): {e}")
    return None


def download_image(url: str, dest: Path) -> bool:
    """画像をダウンロードして保存する"""
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        dest.write_bytes(resp.content)
        return True
    except Exception as e:
        print(f"    [警告] ダウンロード失敗: {e}")
        return False


# ===== manifest.json 生成 =====

def save_manifest(output_dir: Path, entries: list[dict]) -> Path:
    path = output_dir / "manifest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    return path


# ===== メイン =====

def parse_args():
    parser = argparse.ArgumentParser(description="スライド背景画像生成（Pixabay）")
    parser.add_argument("--script",      required=True,  help="台本ファイル名（voice_scripts/内）")
    parser.add_argument("--theme",       required=True,  help="テーマ名（出力フォルダ名）")
    parser.add_argument("--pixabay-key", default=None,   help="Pixabay APIキー（省略時は保存済みキーを使用）")
    parser.add_argument("--max-slides",  type=int, default=MAX_SLIDES, help=f"最大スライド数（デフォルト: {MAX_SLIDES}）")
    parser.add_argument("--save-key",    action="store_true", help="APIキーを~/.secretsに保存する")
    return parser.parse_args()


def main():
    args = parse_args()

    script_path = SCRIPT_DIR / args.script
    if not script_path.exists():
        print(f"エラー: 台本が見つかりません: {script_path}")
        sys.exit(1)

    api_key = load_pixabay_key(args.pixabay_key)
    if args.save_key:
        save_pixabay_key(api_key)

    print(f"\n=== スライド画像生成 ===")
    print(f"台本: {args.script} / テーマ: {args.theme}\n")

    # Step 1: 台本をスライドに分割・間引き
    print("[1/3] 台本をスライドに分割中...")
    script_text = script_path.read_text(encoding="utf-8")
    all_slides = split_script_to_slides(script_text)
    slides = thin_slides(all_slides, args.max_slides)
    print(f"  → {len(all_slides)} 段落を {len(slides)} スライドに間引きました")

    # Step 2: 各スライドの画像を取得
    print(f"\n[2/3] Pixabay から背景画像を取得中...")
    output_dir = OUTPUT_BASE / args.theme / "images"
    output_dir.mkdir(parents=True, exist_ok=True)

    # クエリのキャッシュ（同じクエリを再利用して API 節約）
    query_cache: dict[str, Optional[str]] = {}
    entries = []
    fallback_queries = [
        "landscape calm night",
        "nature peaceful",
        "travel world",
        "sky stars",
    ]
    fallback_idx = 0

    for i, text in enumerate(slides):
        query = extract_keywords(text)
        print(f"  [{i+1:03d}/{len(slides)}] {text[:40]}...")
        print(f"           キーワード: {query}")

        # キャッシュ確認
        if query not in query_cache:
            url = search_pixabay(query, api_key)
            if not url:
                # フォールバック
                fb_query = fallback_queries[fallback_idx % len(fallback_queries)]
                fallback_idx += 1
                url = search_pixabay(fb_query, api_key)
            query_cache[query] = url
            time.sleep(1.0)  # レート制限対策（Pixabay: 5000req/h）

        img_url = query_cache[query]
        img_path = output_dir / f"slide_{i+1:03d}.jpg"

        if img_url and download_image(img_url, img_path):
            # staticFile() は public/ からの相対パスを受け取る
            rel_path = str(img_path.relative_to(PUBLIC_DIR)).replace("\\", "/")
            print(f"           → 保存: {img_path.name}")
        else:
            rel_path = None
            print(f"           → 画像なし（グラデーション背景を使用）")

        entries.append({
            "index": i,
            "text":  text,
            "image": rel_path,
        })

    # Step 3: manifest.json 保存
    print(f"\n[3/3] manifest.json を保存中...")
    manifest_dir = OUTPUT_BASE / args.theme
    manifest_path = save_manifest(manifest_dir, entries)
    print(f"  → {manifest_path}")

    # manifest を public/ にもコピー（Remotion から参照できるよう）
    import shutil
    shutil.copy2(manifest_path, output_dir / "manifest.json")
    print(f"  → Remotion public/ に保存済み: {output_dir}")

    print(f"\n=== 完了 ===")
    print(f"  スライド数: {len(slides)}")
    print(f"  画像フォルダ: {output_dir}")
    print(f"  manifest:    {manifest_path}")
    print(f"\n次のステップ:")
    print(f"  音源化: python3 /Users/deguchishouma/team-info/Remotion/generate_voice.py")
    print(f"  Remotion Root.tsx に CanvaSlideshow コンポジションを追加してレンダリング")


if __name__ == "__main__":
    main()
