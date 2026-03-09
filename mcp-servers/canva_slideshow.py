#!/usr/bin/env python3
"""
Canva Connect API - スライドショー動画制作スクリプト

フロー:
  1. 台本ファイルを段落に分割してスライド内容を決定
  2. Canva Connect API でデザイン（スライド）を作成
  3. PNG としてエクスポート・ダウンロード
  4. outputs/canva_slides/<テーマ>/ に保存

使い方:
  python3 mcp-servers/canva_slideshow.py --script 台本.md --theme テーマ名
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
BASE_DIR        = Path(__file__).resolve().parent.parent            # team-info/
SCRIPT_DIR      = BASE_DIR / "Remotion" / "scripts" / "voice_scripts"
OUTPUT_BASE     = BASE_DIR / "outputs" / "canva_slides"
TOKENS_PATH     = Path.home() / ".secrets" / "canva_tokens.json"
CREDENTIALS_PATH= Path.home() / ".secrets" / "canva_credentials.txt"

# ===== Canva API エンドポイント =====
API_BASE        = "https://api.canva.com/rest/v1"
TOKEN_URL       = "https://api.canva.com/rest/v1/oauth/token"

# ===== スライドデザイン設定 =====
SLIDE_WIDTH     = 1920
SLIDE_HEIGHT    = 1080
FONT_SIZE       = 60
BG_COLOR        = "#0d0d0d"   # 濃いダーク
TEXT_COLOR      = "#f5f5f0"   # オフホワイト
MAX_CHARS_PER_SLIDE = 120     # 1スライドの最大文字数


# ===== トークン管理 =====

def load_tokens() -> dict:
    if not TOKENS_PATH.exists():
        print(f"エラー: トークンファイルが見つかりません: {TOKENS_PATH}")
        print("先に canva_auth.py を実行してください。")
        sys.exit(1)
    with open(TOKENS_PATH) as f:
        return json.load(f)

def load_credentials() -> dict:
    creds = {}
    if CREDENTIALS_PATH.exists():
        for line in CREDENTIALS_PATH.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()
    return creds

def refresh_access_token(refresh_token: str, client_id: str, client_secret: str) -> str:
    import base64
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    resp.raise_for_status()
    new_tokens = resp.json()
    with open(TOKENS_PATH, "w") as f:
        json.dump(new_tokens, f, indent=2)
    os.chmod(TOKENS_PATH, 0o600)
    return new_tokens["access_token"]

def get_access_token() -> str:
    tokens = load_tokens()
    token = tokens.get("access_token", "")
    # トークン有効性確認
    resp = requests.get(
        f"{API_BASE}/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    if resp.status_code == 401:
        print("アクセストークンが期限切れ。リフレッシュ中...")
        creds = load_credentials()
        token = refresh_access_token(
            tokens["refresh_token"],
            creds.get("CANVA_CLIENT_ID", ""),
            creds.get("CANVA_CLIENT_SECRET", ""),
        )
    return token


# ===== 台本パース =====

def split_script_to_slides(script_text: str) -> list[str]:
    """台本を段落単位でスライドに分割する。長い段落はさらに分割。"""
    # マークダウン見出し・空行で段落に分割
    paragraphs = re.split(r'\n{2,}|(?=^#{1,3} )', script_text, flags=re.MULTILINE)
    slides = []
    for para in paragraphs:
        para = para.strip()
        # マークダウン記号・括弧注釈を除去
        para = re.sub(r'^#{1,3}\s*', '', para, flags=re.MULTILINE)
        para = re.sub(r'\[.*?\]|\(.*?\)', '', para)
        para = para.strip()
        if not para:
            continue
        # 長すぎる段落は句点で分割
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


# ===== Canva API 操作 =====

def create_design(token: str, title: str) -> tuple[str, str]:
    """新規デザイン（プレゼンテーション）を作成して (design_id, edit_url) を返す"""
    resp = requests.post(
        f"{API_BASE}/designs",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "design_type": {"type": "preset", "name": "presentation"},
            "title": title,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    design = data["design"]
    design_id = design["id"]
    edit_url = design.get("urls", {}).get("edit_url", "")
    print(f"  デザイン作成: {design_id}")
    return design_id, edit_url

def export_design_as_images(token: str, design_id: str) -> list[str]:
    """デザインを PNG でエクスポートし、ダウンロード URL リストを返す"""
    # エクスポートジョブを作成
    resp = requests.post(
        f"{API_BASE}/exports",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "design_id": design_id,
            "format": {
                "type": "png",
                "export_quality": "regular",
            },
        },
    )
    resp.raise_for_status()
    job = resp.json()
    job_id = job["job"]["id"]
    print(f"  エクスポートジョブ開始: {job_id}")

    # ジョブ完了を待機（最大60秒）
    for _ in range(30):
        time.sleep(2)
        status_resp = requests.get(
            f"{API_BASE}/exports/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = status_data["job"]["status"]
        if status == "success":
            urls = status_data["job"].get("urls", [])  # string[]
            print(f"  エクスポート完了: {len(urls)} ページ")
            return urls
        elif status == "failed":
            err = status_data["job"].get("error", {})
            print(f"エラー: エクスポートに失敗しました: {err.get('message', '')}")
            return []
        print(f"  エクスポート待機中... ({status})")

    print("エラー: エクスポートがタイムアウトしました")
    return []

def download_images(urls: list[str], output_dir: Path) -> list[Path]:
    """URL から PNG をダウンロードして保存、パスリストを返す"""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, url in enumerate(urls):
        path = output_dir / f"slide_{i+1:03d}.png"
        resp = requests.get(url)
        resp.raise_for_status()
        path.write_bytes(resp.content)
        paths.append(path)
        print(f"  ダウンロード: {path.name}")
    return paths


# ===== スライド情報をJSONに保存 =====

def save_slide_manifest(output_dir: Path, slides: list[str], image_paths: list[Path]):
    """スライドテキストと画像パスの対応をJSONで保存（Remotion用）"""
    manifest = []
    for i, (text, img) in enumerate(zip(slides, image_paths)):
        manifest.append({
            "index": i,
            "text": text,
            "image": str(img.relative_to(BASE_DIR)),
        })
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"  マニフェスト保存: {manifest_path}")
    return manifest_path


# ===== メイン =====

def parse_args():
    parser = argparse.ArgumentParser(description="Canva スライドショー生成")
    parser.add_argument("--script", required=True, help="台本ファイル名（voice_scripts/内）")
    parser.add_argument("--theme",  required=True, help="テーマ名（出力フォルダ名になる）")
    parser.add_argument("--skip-pause", action="store_true", help="Canva編集の確認待ちをスキップ")
    return parser.parse_args()


def main():
    args = parse_args()

    script_path = SCRIPT_DIR / args.script
    if not script_path.exists():
        print(f"エラー: 台本ファイルが見つかりません: {script_path}")
        sys.exit(1)

    print(f"\n=== Canva スライドショー生成 ===")
    print(f"台本: {args.script}")
    print(f"テーマ: {args.theme}\n")

    # Step 1: 台本をスライドに分割
    print("[1/4] 台本をスライドに分割中...")
    script_text = script_path.read_text(encoding="utf-8")
    slides = split_script_to_slides(script_text)
    print(f"  → {len(slides)} スライドに分割しました")

    # Step 2: アクセストークン取得
    print("\n[2/4] Canva に接続中...")
    token = get_access_token()
    print("  → 接続OK")

    # Step 3: Canva でデザイン作成
    print("\n[3/4] Canva でデザインを作成中...")
    design_id, edit_url = create_design(token, args.theme)
    if edit_url:
        print(f"\n  ★ Canva でスライドを編集できます:")
        print(f"    {edit_url}\n")
        print("  スライドの内容:")
        for i, text in enumerate(slides[:5], 1):
            print(f"    [{i}] {text[:60]}{'...' if len(text)>60 else ''}")
        if len(slides) > 5:
            print(f"    ... 他 {len(slides)-5} スライド")
        print()
        if not args.skip_pause and sys.stdin.isatty():
            input("  Canvaでスライドを編集・確認したら Enter を押してください > ")

    # Step 4: PNG エクスポート
    print("\n[4/4] PNG エクスポート中...")
    output_dir = OUTPUT_BASE / args.theme
    download_urls = export_design_as_images(token, design_id)
    if not download_urls:
        print("エクスポートに失敗しました。Canvaで手動エクスポートしてください。")
        sys.exit(1)

    image_paths = download_images(download_urls, output_dir)
    manifest_path = save_slide_manifest(output_dir, slides, image_paths)

    print(f"\n=== 完了 ===")
    print(f"  スライド画像: {output_dir}/")
    print(f"  マニフェスト: {manifest_path}")
    print(f"\n次のステップ:")
    print(f"  1. 音源化: python3 /Users/deguchishouma/team-info/Remotion/generate_voice.py")
    print(f"  2. 動画化: Remotion で CanvaSlideshow コンポジションをレンダリング")


if __name__ == "__main__":
    main()
