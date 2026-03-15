#!/usr/bin/env python3
"""
キーワードで画像検索し、上位N枚をダウンロードするスクリプト

内部では常に10枚取得し、以下のフィルタを適用する:
  1. 低解像度（短辺 < 200px）を削除
  2. 顔が検出されないものを削除（OpenCV Haar Cascade）

残った枚数と --count を比較してユーザーに次のアクションを指示する。

使い方:
  python3 image_search_download.py <キーワード> [--count 5] [--out ./downloaded_images]
  python3 image_search_download.py "田中みな実"
  python3 image_search_download.py "cat" --count 3 --out /tmp/cats
"""

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

INTERNAL_FETCH = 10  # 常に内部で取得する枚数
MIN_SHORT_SIDE = 200  # 短辺の最小ピクセル数


def sanitize_dirname(name: str) -> str:
    invalid = r'\/:*?"<>|'
    for ch in invalid:
        name = name.replace(ch, "_")
    return name[:80].strip()


def download_image(url: str, save_path: Path) -> bool:
    """画像URLをダウンロードして保存。成功でTrue"""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        if len(data) < 1024:  # 1KB未満はスキップ
            return False
        save_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"  ✗ {e}", file=sys.stderr)
        return False


def fetch_image_urls(keyword: str, need: int) -> list[str]:
    """Playwright でBing画像検索し、画像URLリストを返す"""
    from playwright.sync_api import sync_playwright

    image_urls: list[str] = []
    search_url = (
        "https://www.bing.com/images/search"
        f"?q={urllib.parse.quote(keyword)}&form=HDRSC3&first=1"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
        )
        page = context.new_page()

        print("📡 Bing画像検索にアクセス中...")
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # 画像カード（.iusc）のJSONメタからオリジナル画像URLを取得
        for el in page.query_selector_all("a.iusc"):
            if len(image_urls) >= need * 3:
                break
            try:
                m = el.get_attribute("m")
                if m:
                    url = json.loads(m).get("murl", "")
                    if url.startswith("http"):
                        image_urls.append(url)
            except Exception:
                pass

        browser.close()

    return image_urls


def filter_images(image_paths: list[Path]) -> tuple[list[Path], list[Path]]:
    """
    低解像度・顔なし画像をフィルタリングする。
    戻り値: (合格リスト, 削除リスト)
    """
    import cv2

    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(cascade_path)

    passed: list[Path] = []
    removed: list[Path] = []

    for p in image_paths:
        img = cv2.imread(str(p))
        if img is None:
            print(f"  [削除] 読み込み不可: {p.name}")
            removed.append(p)
            p.unlink(missing_ok=True)
            continue

        h, w = img.shape[:2]
        short_side = min(h, w)

        # 低解像度チェック
        if short_side < MIN_SHORT_SIDE:
            print(f"  [削除] 解像度不足 ({w}x{h}): {p.name}")
            removed.append(p)
            p.unlink(missing_ok=True)
            continue

        # 顔検出チェック
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=4,
            minSize=(40, 40),
        )
        if len(faces) == 0:
            print(f"  [削除] 顔なし ({w}x{h}): {p.name}")
            removed.append(p)
            p.unlink(missing_ok=True)
            continue

        print(f"  [合格] 顔{len(faces)}件検出 ({w}x{h}): {p.name}")
        passed.append(p)

    return passed, removed


def search_and_download(keyword: str, count: int, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f'🔍 検索キーワード: "{keyword}"')
    print(f"📁 保存先: {out_dir.resolve()}")
    print(f"🎯 目標枚数: {count}枚（内部取得: {INTERNAL_FETCH}枚）\n")

    image_urls = fetch_image_urls(keyword, INTERNAL_FETCH)
    print(f"🔎 {len(image_urls)}件の候補URL取得\n")

    if not image_urls:
        print("❌ 画像URLが見つかりませんでした。")
        sys.exit(1)

    # 常に INTERNAL_FETCH 枚ダウンロード
    downloaded_paths: list[Path] = []
    safe_name = sanitize_dirname(keyword)
    idx = 0

    print(f"⬇️  {INTERNAL_FETCH}枚ダウンロード中...")
    for url in image_urls:
        if len(downloaded_paths) >= INTERNAL_FETCH:
            break

        ext = Path(url.split("?")[0]).suffix.lower()
        if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}:
            ext = ".jpg"

        filename = f"{safe_name}_{idx + 1:02d}{ext}"
        save_path = out_dir / filename

        print(f"[{idx + 1}] {url[:80]}...")
        if download_image(url, save_path):
            size_kb = save_path.stat().st_size // 1024
            print(f"  ✓ 保存: {filename} ({size_kb} KB)")
            downloaded_paths.append(save_path)
        else:
            print("  → 次の候補を試します")

        idx += 1
        time.sleep(0.2)

    print(f"\n📥 ダウンロード完了: {len(downloaded_paths)}枚\n")

    # フィルタリング
    print("🔬 フィルタリング中（解像度チェック + 顔検出）...\n")
    passed, removed = filter_images(downloaded_paths)

    print(f"\n📊 フィルタ結果: {len(downloaded_paths)}枚 → 合格 {len(passed)}枚 / 削除 {len(removed)}枚")
    print(f"📁 保存先: {out_dir.resolve()}\n")

    # 結果に応じたユーザーへの指示
    if len(passed) == count:
        print(f"✅ ちょうど {count}枚の合格画像があります。次のフェーズに進んでください。")
    elif len(passed) > count:
        excess = len(passed) - count
        print(f"⚠️  合格画像が {len(passed)}枚あります（目標: {count}枚）。")
        print(f"   {excess}枚が余分です。不要な画像を手動で削除してから次のフェーズに進んでください。")
        print(f"   削除対象フォルダ: {out_dir.resolve()}")
        print("\n   合格画像一覧:")
        for i, p in enumerate(passed, 1):
            print(f"   [{i}] {p.name}")
    else:
        shortage = count - len(passed)
        print(f"⚠️  合格画像が {len(passed)}枚しかありません（目標: {count}枚）。")
        print(f"   あと {shortage}枚 を手動で追加してから次のフェーズに進んでください。")
        print(f"   追加先フォルダ: {out_dir.resolve()}")
        if passed:
            print("\n   現在の合格画像:")
            for i, p in enumerate(passed, 1):
                print(f"   [{i}] {p.name}")


def main():
    parser = argparse.ArgumentParser(
        description="キーワードでBing画像検索してダウンロード（フィルタリング付き）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("keyword", help="検索キーワード")
    parser.add_argument("--count", "-n", type=int, default=5, help="目標枚数 (デフォルト: 5)")
    parser.add_argument(
        "--out",
        "-o",
        type=Path,
        default=None,
        help="保存先ディレクトリ (デフォルト: ./downloaded_images/<キーワード>)",
    )
    args = parser.parse_args()

    out_dir = args.out or Path("./downloaded_images") / sanitize_dirname(args.keyword)
    search_and_download(args.keyword, args.count, out_dir)


if __name__ == "__main__":
    main()
