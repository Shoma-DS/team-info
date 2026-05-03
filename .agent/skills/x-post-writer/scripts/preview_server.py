# Neon DBから下書きデータを取得してブラウザプレビューに渡すローカルAPIサーバー。
# Discord通知・localtunnelによる公開URLも管理する。
# 起動: bash start_preview.sh（推奨）または python preview_server.py

import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import psycopg2
from psycopg2.extras import RealDictCursor
from runtime_store import load_draft_metadata

PORT = 8765
PREVIEW_DIR = Path(__file__).parent / "preview"

# localtunnel が起動後に環境変数 LT_PUBLIC_URL で渡される
PUBLIC_URL = os.environ.get("LT_PUBLIC_URL", f"http://localhost:{PORT}")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_X_DRAFT", "")


def get_db_conn():
    url = os.environ.get("NEON_DATABASE_URL")
    if not url:
        print("❌ NEON_DATABASE_URL が設定されていません", file=sys.stderr)
        sys.exit(1)
    return psycopg2.connect(url)


def fetch_drafts():
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.draft_id, a.x_username, a.display_name,
                       d.status, d.memo, d.created_at
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                WHERE d.status = 'draft'
                ORDER BY d.created_at DESC
            """)
            drafts = cur.fetchall()
            result = []
            for draft in drafts:
                cur.execute("""
                    SELECT position, content, image_url
                    FROM draft_parts WHERE draft_id = %s ORDER BY position
                """, (str(draft["draft_id"]),))
                parts = cur.fetchall()
                result.append({
                    "draft_id": str(draft["draft_id"]),
                    "x_username": draft["x_username"],
                    "display_name": draft["display_name"] or draft["x_username"],
                    "memo": draft["memo"] or "",
                    "created_at": draft["created_at"].strftime("%Y-%m-%d %H:%M"),
                    "parts": [{"position": p["position"], "content": p["content"], "image_url": p["image_url"]} for p in parts],
                })
            return result
    finally:
        conn.close()


def fetch_draft(draft_id):
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.draft_id, a.x_username, a.display_name,
                       d.status, d.memo, d.created_at
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                WHERE d.draft_id = %s
            """, (draft_id,))
            draft = cur.fetchone()
            if not draft:
                return None
            cur.execute("""
                SELECT position, content, image_url
                FROM draft_parts WHERE draft_id = %s ORDER BY position
            """, (draft_id,))
            parts = cur.fetchall()
            return {
                "draft_id": str(draft["draft_id"]),
                "x_username": draft["x_username"],
                "display_name": draft["display_name"] or draft["x_username"],
                "memo": draft["memo"] or "",
                "created_at": draft["created_at"].strftime("%Y-%m-%d %H:%M"),
                "parts": [{"position": p["position"], "content": p["content"], "image_url": p["image_url"]} for p in parts],
            }
    finally:
        conn.close()


def send_discord(draft_id, main_content, x_username):
    if not DISCORD_WEBHOOK:
        return False, "DISCORD_WEBHOOK_X_DRAFT が未設定"

    preview_url = f"{PUBLIC_URL}?draft={draft_id}"
    metadata = load_draft_metadata(str(draft_id)) or {}
    image_prompt_block = ""
    image_prompts = metadata.get("image_prompts") or []
    if image_prompts:
        first = image_prompts[0]
        image_prompt_block = (
            "\n\n**画像プロンプト案内:**\n"
            f"- file: {first.get('file_path', 'なし')}\n"
            f"- copy: {str(first.get('copy', ''))[:120]}\n"
            "```"
            f"\n{str(first.get('prompt', ''))[:700]}\n"
            "```"
        )

    message = {
        "content": (
            f"📝 **@{x_username}** の下書きが投稿準備されました\n\n"
            f"🔗 プレビュー: {preview_url}\n\n"
            f"**投稿内容（メイン）:**\n"
            f"```\n{main_content[:800]}\n```"
            f"{image_prompt_block}"
        )
    }

    body = json.dumps(message).encode("utf-8")
    req = urllib.request.Request(
        DISCORD_WEBHOOK,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status in (200, 204), None
    except Exception as e:
        return False, str(e)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type):
        try:
            body = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path in ("/", "/index.html"):
            self.send_file(PREVIEW_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self.send_file(PREVIEW_DIR / "style.css", "text/css")
        elif path == "/app.js":
            self.send_file(PREVIEW_DIR / "app.js", "application/javascript")
        elif path == "/api/drafts":
            try:
                self.send_json(fetch_drafts())
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/draft":
            draft_id = qs.get("id", [None])[0]
            if not draft_id:
                self.send_json({"error": "id パラメータが必要です"}, 400)
                return
            try:
                data = fetch_draft(draft_id)
                self.send_json(data if data else {"error": "見つかりません"}, 200 if data else 404)
            except Exception as e:
                self.send_json({"error": str(e)}, 500)
        elif path == "/api/public-url":
            self.send_json({"url": PUBLIC_URL})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}

        if path == "/api/notify":
            draft_id = body.get("draft_id")
            main_content = body.get("main_content", "")
            x_username = body.get("x_username", "")
            ok, err = send_discord(draft_id, main_content, x_username)
            if ok:
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": err}, 500)
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    print(f"✅ プレビューサーバー起動: http://localhost:{PORT}")
    if PUBLIC_URL != f"http://localhost:{PORT}":
        print(f"🌐 公開URL: {PUBLIC_URL}")
    if not DISCORD_WEBHOOK:
        print("⚠️  DISCORD_WEBHOOK_X_DRAFT が未設定のため Discord 通知は無効です")
    print("   終了するには Ctrl+C を押してください\n")
    server = HTTPServer(("localhost", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
