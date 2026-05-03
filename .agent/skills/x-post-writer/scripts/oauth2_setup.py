# X OAuth 2.0 User Context のアクセストークンを取得する一回限りのセットアップスクリプト。
# 取得したトークンは settings.local.json の env ブロックへ追記する手順を案内する。
# 使い方: python oauth2_setup.py --account GUTARA

import argparse
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import tweepy

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "accounts_config.json"
NGROK_DOMAIN = "zinciferous-preludiously-draven.ngrok-free.dev"
REDIRECT_URI = f"https://{NGROK_DOMAIN}/oauth2/callback"
SCOPES = ["bookmark.read", "tweet.read", "users.read", "offline.access"]
CALLBACK_PORT = 8766
CALLBACK_PATH = "/oauth2/callback"


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        raw = "".join(l for l in f if not l.strip().startswith("//"))
        return json.loads(raw)


class CallbackHandler(BaseHTTPRequestHandler):
    auth_code = None
    state_received = None

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == CALLBACK_PATH:
            qs = parse_qs(parsed.query)
            CallbackHandler.auth_code = qs.get("code", [None])[0]
            CallbackHandler.state_received = qs.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                "<html><body><h2>✅ 認証完了！このタブを閉じてターミナルに戻ってください。</h2></body></html>".encode()
            )
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def run_callback_server():
    server = HTTPServer(("localhost", CALLBACK_PORT), CallbackHandler)
    server.handle_request()
    server.server_close()


def main():
    parser = argparse.ArgumentParser(description="X OAuth 2.0 セットアップ")
    parser.add_argument("--account", default="GUTARA", help="アカウントID")
    args = parser.parse_args()

    config = load_config()
    account_cfg = next((a for a in config["accounts"] if a["id"] == args.account), None)
    if not account_cfg:
        print(f"❌ アカウント '{args.account}' が見つかりません", file=sys.stderr)
        sys.exit(1)

    # Client ID / Secret を環境変数から取得
    account_id = account_cfg["id"]
    client_id = os.environ.get(f"X_OAUTH2_CLIENT_ID_{account_id}") or os.environ.get("X_OAUTH2_CLIENT_ID")
    client_secret = os.environ.get(f"X_OAUTH2_CLIENT_SECRET_{account_id}") or os.environ.get("X_OAUTH2_CLIENT_SECRET")

    if not client_id:
        print(f"""
❌ OAuth 2.0 Client ID が未設定です。

X Developer Portal でアプリの OAuth 2.0 を有効にして、
以下の環境変数を settings.local.json の env ブロックに追加してください:

  "X_OAUTH2_CLIENT_ID_{account_id}": "ここにClient IDを貼り付け"
  "X_OAUTH2_CLIENT_SECRET_{account_id}": "ここにClient Secretを貼り付け"

Claude Code を再起動してからもう一度実行してください。
""", file=sys.stderr)
        sys.exit(1)

    print(f"🔐 @{account_cfg['x_username']} の OAuth 2.0 認証を開始します")
    print(f"   スコープ: {', '.join(SCOPES)}")
    print(f"\n⚠️  事前に以下のコマンドで ngrok を起動してください（別ターミナルで）:")
    print(f"   ngrok http {CALLBACK_PORT} --domain={NGROK_DOMAIN}")
    print(f"   起動後、Enterキーを押して続行してください...")
    input()

    handler = tweepy.OAuth2UserHandler(
        client_id=client_id,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=client_secret or None,
    )

    auth_url = handler.get_authorization_url()

    # コールバックサーバーをバックグラウンドで起動
    t = threading.Thread(target=run_callback_server, daemon=True)
    t.start()

    print("🌐 ブラウザを開いてXでログイン・認証してください...")
    webbrowser.open(auth_url)
    print(f"   （ブラウザが開かない場合は以下のURLを手動でコピーしてください）")
    print(f"   {auth_url}\n")
    print("   認証完了まで待機中...")

    t.join(timeout=120)

    if not CallbackHandler.auth_code:
        print("❌ 120秒以内に認証が完了しませんでした。もう一度実行してください。", file=sys.stderr)
        sys.exit(1)

    print("✅ 認証コードを受信しました。トークンを取得中...")

    try:
        token = handler.fetch_token(
            f"{REDIRECT_URI}?code={CallbackHandler.auth_code}&state={CallbackHandler.state_received}"
        )
    except Exception as e:
        print(f"❌ トークン取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    print(f"""
✅ OAuth 2.0 認証が完了しました！

以下の環境変数を settings.local.json の env ブロックに追加してください:

  "X_BOOKMARKS_ACCESS_TOKEN_{account_id}": "{access_token}"
""")

    if refresh_token:
        print(f'  "X_BOOKMARKS_REFRESH_TOKEN_{account_id}": "{refresh_token}"')
        print()

    print("追加後に Claude Code を再起動してください。")
    print("その後 scheduled_draft_pipeline.py を実行するとブックマーク取得が動きます。")


if __name__ == "__main__":
    main()
