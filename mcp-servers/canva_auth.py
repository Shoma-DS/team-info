#!/usr/bin/env python3
"""
Canva Connect API - OAuthアクセストークン取得スクリプト
PKCE (S256) フローでアクセストークンを取得し、~/.secrets/canva_tokens.json に保存する
"""

import base64
import hashlib
import json
import os
import secrets
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

# ===== 設定 =====
REDIRECT_URI  = "http://127.0.0.1:3001/oauth/redirect"
SCOPES        = "design:content:write asset:write design:content:read asset:read"

AUTH_URL      = "https://www.canva.com/api/oauth/authorize"
TOKEN_URL     = "https://api.canva.com/rest/v1/oauth/token"
SAVE_PATH     = os.path.expanduser("~/.secrets/canva_tokens.json")
CREDENTIALS_PATH = Path.home() / ".secrets" / "canva_credentials.txt"


def load_credentials() -> tuple[str, str]:
    client_id = os.getenv("CANVA_CLIENT_ID", "").strip()
    client_secret = os.getenv("CANVA_CLIENT_SECRET", "").strip()

    if CREDENTIALS_PATH.exists():
        for line in CREDENTIALS_PATH.read_text().splitlines():
            if "=" not in line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if key == "CANVA_CLIENT_ID" and not client_id:
                client_id = value
            if key == "CANVA_CLIENT_SECRET" and not client_secret:
                client_secret = value

    if client_id and client_secret:
        return client_id, client_secret

    print("エラー: Canva の ID または秘密の文字が見つかりません。")
    print("環境変数 CANVA_CLIENT_ID / CANVA_CLIENT_SECRET を入れてください。")
    print(f"または {CREDENTIALS_PATH} に書いてください。")
    sys.exit(1)

# ===== PKCE ユーティリティ =====

def generate_code_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()

def generate_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()

# ===== ローカル受信サーバー =====

received: dict = {}

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        received["code"]  = params.get("code",  [None])[0]
        received["state"] = params.get("state", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            "<h2>認証完了！このタブを閉じてターミナルに戻ってください。</h2>".encode()
        )

    def log_message(self, *args):
        pass  # ログ抑制

def start_callback_server(port: int = 3001):
    server = HTTPServer(("127.0.0.1", port), CallbackHandler)
    thread = threading.Thread(target=server.handle_request)
    thread.daemon = True
    thread.start()
    return server

# ===== トークン交換 =====

def exchange_code_for_token(
    code: str,
    verifier: str,
    client_id: str,
    client_secret: str,
) -> dict:
    auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type":    "authorization_code",
            "code":          code,
            "redirect_uri":  REDIRECT_URI,
            "code_verifier": verifier,
        },
    )
    resp.raise_for_status()
    return resp.json()

# ===== メイン =====

def main():
    print("Canva OAuth 認証を開始します...\n")

    client_id, client_secret = load_credentials()
    verifier  = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    state     = secrets.token_urlsafe(16)

    params = {
        "code_challenge_method": "s256",
        "response_type":         "code",
        "client_id":             client_id,
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "code_challenge":        challenge,
        "state":                 state,
    }
    auth_url = f"{AUTH_URL}?{urlencode(params)}"

    print("ローカルコールバックサーバーを起動中...")
    start_callback_server(port=3001)

    print("ブラウザでCanva認証ページを開きます...")
    webbrowser.open(auth_url)
    print("ブラウザでCanvaにログインして許可してください。\n")

    # コールバック待機
    import time
    for _ in range(120):  # 最大2分待機
        if received.get("code"):
            break
        time.sleep(1)

    if not received.get("code"):
        print("エラー: タイムアウトしました。もう一度実行してください。")
        return

    print("認証コードを受信しました。トークンを取得中...")
    try:
        tokens = exchange_code_for_token(
            received["code"],
            verifier,
            client_id,
            client_secret,
        )
    except Exception as e:
        print(f"エラー: トークン取得に失敗しました: {e}")
        return

    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    with open(SAVE_PATH, "w") as f:
        json.dump(tokens, f, indent=2, ensure_ascii=False)
    os.chmod(SAVE_PATH, 0o600)

    print(f"\n完了！トークンを保存しました: {SAVE_PATH}")
    print(f"  access_token : {tokens.get('access_token', '')[:20]}...")
    if "refresh_token" in tokens:
        print(f"  refresh_token: {tokens['refresh_token'][:20]}...")

if __name__ == "__main__":
    main()
