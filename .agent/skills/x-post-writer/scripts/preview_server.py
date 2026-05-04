# Neon DBから下書きデータを取得してブラウザプレビューに渡すローカルAPIサーバー。
# Discord通知・localtunnelによる公開URLも管理する。
# 起動: bash start_preview.sh（推奨）または python preview_server.py

import json
import os
import sys
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote as urlquote
import psycopg2
from psycopg2.extras import RealDictCursor
from runtime_store import load_draft_metadata

PORT = 8765
PREVIEW_DIR   = Path(__file__).parent / "preview"
BOOKMARKS_FILE = Path(__file__).parent / "bookmarks_latest.json"

PUBLIC_URL = os.environ.get("LT_PUBLIC_URL", f"http://localhost:{PORT}")
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK_X_DRAFT", "")

# oauth2_setup.py からのコールバックを一時保存する（プロセス内共有）
_oauth2_pending: dict = {}


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
                       a.profile_image_url,
                       d.status, d.memo, d.created_at, d.published_at
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                ORDER BY d.created_at DESC
            """)
            drafts = cur.fetchall()
            result = []
            for draft in drafts:
                cur.execute("""
                    SELECT part_id, position, content, image_url
                    FROM draft_parts WHERE draft_id = %s ORDER BY position
                """, (str(draft["draft_id"]),))
                parts = cur.fetchall()
                result.append({
                    "draft_id": str(draft["draft_id"]),
                    "x_username": draft["x_username"],
                    "display_name": draft["display_name"] or draft["x_username"],
                    "profile_image_url": draft["profile_image_url"] or "",
                    "memo": draft["memo"] or "",
                    "status": draft["status"] or "draft",
                    "created_at": draft["created_at"].strftime("%Y-%m-%d %H:%M"),
                    "published_at": draft["published_at"].strftime("%Y-%m-%d %H:%M") if draft["published_at"] else None,
                    "parts": [
                        {
                            "part_id": str(p["part_id"]),
                            "position": p["position"],
                            "content": p["content"],
                            "image_url": p["image_url"],
                        }
                        for p in parts
                    ],
                })
            return result
    finally:
        conn.close()


def _load_original_tweet(draft_id: str) -> dict | None:
    """draft-metadata と bookmarks_latest.json から元ツイート（スレッド含む）を返す。"""
    metadata = load_draft_metadata(str(draft_id))
    if not metadata:
        return None
    tweet_id = str(metadata.get("bookmark_tweet_id") or "")
    author   = metadata.get("author_username") or ""
    if not tweet_id:
        return None
    if BOOKMARKS_FILE.exists():
        try:
            data      = json.loads(BOOKMARKS_FILE.read_text(encoding="utf-8"))
            bookmarks = data.get("bookmarks", [])
            for bm in bookmarks:
                if str(bm.get("tweet_id")) == tweet_id:
                    username     = bm.get("author_username") or author
                    raw_parts    = bm.get("thread_parts") or []
                    # 各パーツに author_username を付与してフロントでURL生成できるようにする
                    thread_parts = [
                        {**p, "author_username": username,
                         "tweet_url": f"https://x.com/{username}/status/{p['tweet_id']}"}
                        for p in raw_parts
                    ]
                    return {
                        "tweet_id":        tweet_id,
                        "tweet_url":       f"https://x.com/{username}/status/{tweet_id}",
                        "text":            bm.get("text") or "",
                        "author_username": username,
                        "author_name":     bm.get("author_name") or "",
                        "thread_parts":    thread_parts,
                    }
        except Exception:
            pass
    # bookmarks_latest にないときは tweet_id と author だけ返す
    tweet_url = f"https://x.com/{author}/status/{tweet_id}" if author else ""
    return {
        "tweet_id":        tweet_id,
        "tweet_url":       tweet_url,
        "text":            None,
        "author_username": author,
        "author_name":     "",
        "thread_parts":    [],
    }


def fetch_draft(draft_id):
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT d.draft_id, a.x_username, a.display_name,
                       a.profile_image_url,
                       d.status, d.memo, d.created_at, d.published_at
                FROM drafts d
                JOIN accounts a ON d.account_id = a.account_id
                WHERE d.draft_id = %s
            """, (draft_id,))
            draft = cur.fetchone()
            if not draft:
                return None
            cur.execute("""
                SELECT part_id, position, content, image_url
                FROM draft_parts WHERE draft_id = %s ORDER BY position
            """, (draft_id,))
            parts = cur.fetchall()
            metadata      = load_draft_metadata(str(draft["draft_id"])) or {}
            image_prompts = metadata.get("image_prompts") or []
            return {
                "draft_id": str(draft["draft_id"]),
                "x_username": draft["x_username"],
                "display_name": draft["display_name"] or draft["x_username"],
                "profile_image_url": draft["profile_image_url"] or "",
                "memo": draft["memo"] or "",
                "status": draft["status"] or "draft",
                "created_at": draft["created_at"].strftime("%Y-%m-%d %H:%M"),
                "published_at": draft["published_at"].strftime("%Y-%m-%d %H:%M") if draft["published_at"] else None,
                "parts": [
                    {
                        "part_id": str(p["part_id"]),
                        "position": p["position"],
                        "content": p["content"],
                        "image_url": p["image_url"],
                    }
                    for p in parts
                ],
                "image_prompts": image_prompts,
                "original_tweet": _load_original_tweet(str(draft["draft_id"])),
            }
    finally:
        conn.close()


def delete_draft(draft_id):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM draft_parts WHERE draft_id = %s", (draft_id,))
            cur.execute("DELETE FROM drafts WHERE draft_id = %s", (draft_id,))
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def add_draft_part(draft_id, content):
    conn = get_db_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT COALESCE(MAX(position), 0) AS max_pos FROM draft_parts WHERE draft_id = %s",
                (draft_id,),
            )
            next_pos = cur.fetchone()["max_pos"] + 1
            cur.execute(
                "INSERT INTO draft_parts (draft_id, position, content) VALUES (%s, %s, %s)",
                (draft_id, next_pos, content),
            )
            conn.commit()
            return True
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_part_content(part_id, content):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE draft_parts SET content = %s WHERE part_id = %s",
                (content, part_id),
            )
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_draft_status(draft_id, status):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            if status == "published":
                cur.execute(
                    "UPDATE drafts SET status = %s, published_at = NOW() WHERE draft_id = %s",
                    (status, draft_id),
                )
            else:
                cur.execute(
                    "UPDATE drafts SET status = %s, published_at = NULL WHERE draft_id = %s",
                    (status, draft_id),
                )
            conn.commit()
            return cur.rowcount > 0
    except Exception:
        conn.rollback()
        raise
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


def get_oembed_html(tweet_url: str) -> str | None:
    """X の oEmbed API からレンダリング用 HTML を取得する。"""
    api = f"https://publish.twitter.com/oembed?url={urlquote(tweet_url)}&omit_script=true&theme=dark&dnt=true"
    try:
        req = urllib.request.Request(api, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("html") or None
    except Exception:
        return None


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

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
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
        elif path == "/api/oembed":
            tweet_url = qs.get("url", [None])[0]
            if not tweet_url:
                self.send_json({"error": "url パラメータが必要です"}, 400)
                return
            html = get_oembed_html(tweet_url)
            if html:
                self.send_json({"ok": True, "html": html})
            else:
                self.send_json({"ok": False, "error": "oEmbed取得失敗"})
        elif path == "/oauth2/callback":
            # oauth2_setup.py からのリダイレクトを受け取り、コードを一時保存する
            code  = qs.get("code",  [None])[0]
            state = qs.get("state", [None])[0]
            _oauth2_pending["code"]  = code
            _oauth2_pending["state"] = state
            body = "<html><body><h2>✅ 認証完了！このタブを閉じてターミナルに戻ってください。</h2></body></html>".encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/api/oauth2-callback":
            # oauth2_setup.py がポーリングしてコードを取得する。取得後はクリア
            if _oauth2_pending.get("code"):
                data = dict(_oauth2_pending)
                _oauth2_pending.clear()
                self.send_json({"ok": True, **data})
            else:
                self.send_json({"ok": False})
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/api/draft":
            draft_id = qs.get("id", [None])[0]
            if not draft_id:
                self.send_json({"error": "id パラメータが必要です"}, 400)
                return
            try:
                delete_draft(draft_id)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/draft/part":
            body = self.read_body()
            part_id = body.get("part_id")
            content = body.get("content")
            if not part_id or content is None:
                self.send_json({"error": "part_id と content が必要です"}, 400)
                return
            try:
                ok = update_part_content(part_id, content)
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_PATCH(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/draft/status":
            body = self.read_body()
            draft_id = body.get("draft_id")
            status = body.get("status")
            if not draft_id or status not in ("draft", "published"):
                self.send_json({"error": "draft_id と status (draft|published) が必要です"}, 400)
                return
            try:
                ok = update_draft_status(draft_id, status)
                self.send_json({"ok": ok})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self.read_body()

        if path == "/api/notify":
            draft_id = body.get("draft_id")
            main_content = body.get("main_content", "")
            x_username = body.get("x_username", "")
            ok, err = send_discord(draft_id, main_content, x_username)
            if ok:
                self.send_json({"ok": True})
            else:
                self.send_json({"ok": False, "error": err}, 500)
        elif path == "/api/draft/part":
            draft_id = body.get("draft_id")
            content  = (body.get("content") or "").strip()
            if not draft_id or not content:
                self.send_json({"error": "draft_id と content が必要です"}, 400)
                return
            try:
                add_draft_part(draft_id, content)
                self.send_json({"ok": True})
            except Exception as e:
                self.send_json({"ok": False, "error": str(e)}, 500)
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
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました")
