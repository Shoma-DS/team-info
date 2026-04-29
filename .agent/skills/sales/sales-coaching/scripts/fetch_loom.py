"""
Loom OAuth 2.0 認証 + 文字起こし取得

初回実行時: ブラウザが開いてLoomログイン → 認証後トークンを自動保存
2回目以降: 保存済みトークンを使って自動実行

必要な環境変数（.env）:
  LOOM_CLIENT_ID     : developers.loom.com で取得したClient ID
  LOOM_CLIENT_SECRET : developers.loom.com で取得したClient Secret
"""

import json
import os
import re
import secrets
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

LOOM_CLIENT_ID = os.environ.get("LOOM_CLIENT_ID", "")
LOOM_CLIENT_SECRET = os.environ.get("LOOM_CLIENT_SECRET", "")
LOOM_API_BASE = "https://api.loom.com/v1"
LOOM_AUTH_URL = "https://api.loom.com/v1/oauth2/authorize"
LOOM_TOKEN_URL = "https://api.loom.com/v1/oauth2/token"
REDIRECT_URI = "http://localhost:8765/callback"

TOKEN_FILE = Path(__file__).resolve().parents[5] / ".loom_token.json"


# ── トークン管理 ──────────────────────────────────

def _save_token(token_data: dict) -> None:
    token_data["saved_at"] = int(time.time())
    TOKEN_FILE.write_text(json.dumps(token_data, indent=2), encoding="utf-8")


def _load_token() -> dict | None:
    if TOKEN_FILE.exists():
        return json.loads(TOKEN_FILE.read_text(encoding="utf-8"))
    return None


def _is_expired(token_data: dict) -> bool:
    saved_at = token_data.get("saved_at", 0)
    expires_in = token_data.get("expires_in", 3600)
    # 5分前に期限切れとみなす
    return time.time() > saved_at + expires_in - 300


def _refresh_token(token_data: dict) -> dict:
    resp = requests.post(
        LOOM_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": token_data["refresh_token"],
            "client_id": LOOM_CLIENT_ID,
            "client_secret": LOOM_CLIENT_SECRET,
        },
        timeout=30,
    )
    resp.raise_for_status()
    new_token = resp.json()
    # refresh_tokenが返らない場合は既存のものを引き継ぐ
    if "refresh_token" not in new_token:
        new_token["refresh_token"] = token_data["refresh_token"]
    _save_token(new_token)
    return new_token


# ── OAuth 認証フロー（初回のみ）────────────────────

class _CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            _CallbackHandler.auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body><h2>認証完了！このタブを閉じてターミナルに戻ってください。</h2></body></html>".encode()
            )
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # ローカルサーバーのログを抑制


def _authorize() -> dict:
    state = secrets.token_urlsafe(16)
    params = {
        "client_id": LOOM_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "videos:read",
        "state": state,
    }
    auth_url = f"{LOOM_AUTH_URL}?{urlencode(params)}"

    print("\nブラウザが開きます。Loomにログインして許可してください...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8765), _CallbackHandler)
    server.timeout = 120
    print("認証待機中（最大2分）...")
    while _CallbackHandler.auth_code is None:
        server.handle_request()
    server.server_close()

    code = _CallbackHandler.auth_code
    _CallbackHandler.auth_code = None

    resp = requests.post(
        LOOM_TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": LOOM_CLIENT_ID,
            "client_secret": LOOM_CLIENT_SECRET,
        },
        timeout=30,
    )
    resp.raise_for_status()
    token_data = resp.json()
    _save_token(token_data)
    print("認証完了。トークンを保存しました。")
    return token_data


def _get_access_token() -> str:
    if not LOOM_CLIENT_ID or not LOOM_CLIENT_SECRET:
        print("エラー: LOOM_CLIENT_ID または LOOM_CLIENT_SECRET が未設定です")
        raise SystemExit(1)

    token_data = _load_token()
    if token_data is None:
        print("初回認証を開始します...")
        token_data = _authorize()
    elif _is_expired(token_data):
        print("トークンを更新中...")
        try:
            token_data = _refresh_token(token_data)
        except Exception:
            print("リフレッシュ失敗。再認証します...")
            token_data = _authorize()

    return token_data["access_token"]


# ── メイン関数 ───────────────────────────────────

def _extract_video_id(loom_url_or_id: str) -> str:
    match = re.search(r"loom\.com/share/([a-zA-Z0-9]+)", loom_url_or_id)
    if match:
        return match.group(1)
    if re.fullmatch(r"[a-zA-Z0-9]+", loom_url_or_id):
        return loom_url_or_id
    raise ValueError(f"Loom URLまたはIDとして認識できません: {loom_url_or_id}")


def fetch_transcript(loom_url_or_id: str) -> str:
    access_token = _get_access_token()
    video_id = _extract_video_id(loom_url_or_id)
    url = f"{LOOM_API_BASE}/recordings/{video_id}/transcripts"
    headers = {"Authorization": f"Bearer {access_token}"}

    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 401:
        # トークン無効なら再認証
        print("トークンが無効です。再認証します...")
        TOKEN_FILE.unlink(missing_ok=True)
        access_token = _get_access_token()
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code == 404:
        raise RuntimeError(f"動画が見つかりません（または文字起こし未生成）: {video_id}")
    resp.raise_for_status()

    data = resp.json()
    transcript_data = (
        data.get("transcripts")
        or data.get("transcript")
        or data.get("data", {}).get("transcripts", [])
    )
    if isinstance(transcript_data, list):
        return "\n".join(
            item.get("text", str(item)) if isinstance(item, dict) else str(item)
            for item in transcript_data
        )
    return str(transcript_data)


def get_video_id(loom_url_or_id: str) -> str:
    return _extract_video_id(loom_url_or_id)
