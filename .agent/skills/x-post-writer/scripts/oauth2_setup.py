# X OAuth 2.0 User Context のアクセストークンを取得する一回限りのセットアップスクリプト。
# コールバックはプレビューサーバー（port 8765）の /oauth2/callback で受け取る。
# ngrok の別起動は不要（start_preview.sh で起動済みの ngrok をそのまま使う）。
# 使い方: python oauth2_setup.py --account GUTARA

import argparse
import json
import os
import sys
import time
import webbrowser
from pathlib import Path

import requests
import tweepy

SCRIPT_DIR  = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "accounts_config.json"

NGROK_DOMAIN  = "zinciferous-preludiously-draven.ngrok-free.dev"
REDIRECT_URI  = f"https://{NGROK_DOMAIN}/oauth2/callback"
PREVIEW_API   = "http://localhost:8765/api/oauth2-callback"
SCOPES        = ["bookmark.read", "tweet.read", "users.read", "offline.access"]
POLL_INTERVAL = 2    # 秒
POLL_TIMEOUT  = 180  # 秒


def load_config():
    with open(CONFIG_FILE, encoding="utf-8") as f:
        raw = "".join(l for l in f if not l.strip().startswith("//"))
        return json.loads(raw)


def save_tokens_to_settings(account_id, access_token, refresh_token=None):
    settings_file = SCRIPT_DIR.parent.parent.parent.parent / ".claude" / "settings.local.json"
    if not settings_file.exists():
        print("⚠️  settings.local.json が見つからないため、ファイルへの保存をスキップします", file=sys.stderr)
        return
    try:
        config = json.loads(settings_file.read_text(encoding="utf-8"))
        env = config.setdefault("env", {})
        env[f"X_BOOKMARKS_ACCESS_TOKEN_{account_id}"] = access_token
        if refresh_token:
            env[f"X_BOOKMARKS_REFRESH_TOKEN_{account_id}"] = refresh_token
        settings_file.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print("💾 settings.local.json にトークンを保存しました")
    except Exception as e:
        print(f"⚠️  settings.local.json の更新に失敗しました: {e}", file=sys.stderr)


def poll_callback():
    """プレビューサーバーから OAuth コールバックのコードを受け取るまでポーリングする。"""
    deadline = time.time() + POLL_TIMEOUT
    while time.time() < deadline:
        try:
            r = requests.get(PREVIEW_API, timeout=5)
            data = r.json()
            if data.get("ok") and data.get("code"):
                return data["code"], data.get("state")
        except requests.RequestException:
            pass
        time.sleep(POLL_INTERVAL)
    return None, None


def main():
    parser = argparse.ArgumentParser(description="X OAuth 2.0 セットアップ")
    parser.add_argument("--account", default="GUTARA", help="アカウントID")
    args = parser.parse_args()

    config = load_config()
    account_cfg = next((a for a in config["accounts"] if a["id"] == args.account), None)
    if not account_cfg:
        print(f"❌ アカウント '{args.account}' が見つかりません", file=sys.stderr)
        sys.exit(1)

    account_id    = account_cfg["id"]
    client_id     = os.environ.get(f"X_OAUTH2_CLIENT_ID_{account_id}") or os.environ.get("X_OAUTH2_CLIENT_ID")
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

    # プレビューサーバーが起動しているか確認
    try:
        requests.get("http://localhost:8765/api/public-url", timeout=3)
    except requests.RequestException:
        print(
            "❌ プレビューサーバーが起動していません。\n"
            "   先に以下を実行してください:\n"
            f"   bash \"$TEAM_INFO_ROOT/.agent/skills/x-post-writer/scripts/start_preview.sh\"",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"🔐 @{account_cfg['x_username']} の OAuth 2.0 認証を開始します")
    print(f"   スコープ: {', '.join(SCOPES)}")
    print(f"   コールバック: {REDIRECT_URI}\n")

    handler = tweepy.OAuth2UserHandler(
        client_id=client_id,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        client_secret=client_secret or None,
    )

    auth_url = handler.get_authorization_url()

    print("🌐 ブラウザを開いてXでログイン・認証してください...")
    webbrowser.open(auth_url)
    print(f"   （ブラウザが開かない場合は以下のURLを手動でコピーしてください）")
    print(f"   {auth_url}\n")
    print(f"   認証完了まで待機中（最大{POLL_TIMEOUT}秒）...")

    code, state = poll_callback()

    if not code:
        print(f"❌ {POLL_TIMEOUT}秒以内に認証が完了しませんでした。もう一度実行してください。", file=sys.stderr)
        sys.exit(1)

    print("✅ 認証コードを受信しました。トークンを取得中...")

    try:
        token = handler.fetch_token(
            f"{REDIRECT_URI}?code={code}&state={state}"
        )
    except Exception as e:
        print(f"❌ トークン取得に失敗しました: {e}", file=sys.stderr)
        sys.exit(1)

    access_token  = token.get("access_token")
    refresh_token = token.get("refresh_token")

    save_tokens_to_settings(account_id, access_token, refresh_token)

    print(f"\n✅ OAuth 2.0 認証が完了しました！")
    print(f"   アクセストークンとリフレッシュトークンを settings.local.json に保存しました。")
    print(f"   Claude Code を再起動してから sync_profile_images.py を実行してください。\n")


if __name__ == "__main__":
    main()
