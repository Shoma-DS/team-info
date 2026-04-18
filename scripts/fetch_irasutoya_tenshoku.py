#!/usr/bin/env python3
import sys
import os
import urllib.parse
import urllib.request
import re
from pathlib import Path

def search_irasutoya_ddg(keyword):
    query = f"site:irasutoya.com {keyword}"
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        # DDG proxy URLs
        matches = re.findall(r'src="(//external-content\.duckduckgo\.com/iu/\?u=[^"]+)"', html)
        urls = ["https:" + m for m in matches]
        return urls
    except Exception as e:
        print(f"DDG検索エラー: {e}")
        return []

def download_image(url, dest_path):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        dest_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"DLエラー: {e}")
        return False

OUT_DIR = Path(__file__).resolve().parents[1] / "Remotion" / "my-video" / "public" / "viral" / "転職ショート_20260416"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_PLAN = [
    {"filename": "hook.png", "keyword": "退職 ショック 女性"},
    {"filename": "s1.png", "keyword": "無視する スルー 会議"},
    {"filename": "s2.png", "keyword": "過労 疲労 評価"},
    {"filename": "s3.png", "keyword": "怒る 上司 無能"}
]

def fetch_assets():
    for asset in ASSETS_PLAN:
        target_path = OUT_DIR / asset["filename"]
        print(f"[{asset['filename']}] をキーワード '{asset['keyword']}' で検索中... (DDG)")
        candidates = search_irasutoya_ddg(asset['keyword'])
        if not candidates:
            print(f"  -> 画像が見つかりませんでした。")
            continue
        
        target_url = candidates[0]
        print(f"  -> ダウンロード開始: {target_url}")
        success = download_image(target_url, target_path)
        if success:
            print(f"  -> 保存完了: {target_path}")
        else:
            print(f"  -> 保存失敗: {target_path}")

if __name__ == '__main__':
    fetch_assets()
