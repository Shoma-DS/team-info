# Xブックマークから下書き生成を定時自動化するオーケストレータ。
# Codex を優先し、失敗や token/context 制限時は Claude Code にフォールバックする。
# 保存、state 管理、Discord 通知、画像プロンプトファイル保存はこのスクリプトが担当する。

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from draft_manager import save_draft
from runtime_store import (
    get_logs_dir,
    load_processed_bookmarks,
    save_processed_bookmarks,
    save_draft_metadata,
    write_image_prompt_file,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_DIR = Path(__file__).parent
FETCH_BOOKMARKS_SCRIPT = SCRIPT_DIR / "fetch_bookmarks.py"
BOOKMARKS_FILE = SCRIPT_DIR / "bookmarks_latest.json"
SCHEMA_FILE = SCRIPT_DIR / "draft_generation_schema.json"
CLAUDE_SETTINGS_FILE = REPO_ROOT / ".claude" / "settings.local.json"
DEFAULT_PREVIEW_URL = "https://zinciferous-preludiously-draven.ngrok-free.dev"
DISCORD_WEBHOOK_ENV = "DISCORD_WEBHOOK_X_DRAFT"
TOKEN_LIMIT_PATTERNS = (
    r"token limit",
    r"context length",
    r"maximum context length",
    r"too many tokens",
    r"prompt is too long",
)


class JobError(RuntimeError):
    pass


_IS_TTY = sys.stdout.isatty()


class _Spinner:
    """ステップ実行中にスピナーを表示し、完了/失敗を1行で上書きする。"""

    _FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"

    def __init__(self, message: str) -> None:
        self._msg = message
        self._ok_msg: str | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    def update(self, message: str) -> None:
        self._msg = message

    def finish_ok(self, message: str) -> None:
        self._ok_msg = message

    def __enter__(self) -> "_Spinner":
        if _IS_TTY:
            self._running = True
            self._thread = threading.Thread(target=self._spin, daemon=True)
            self._thread.start()
        else:
            print(f"  → {self._msg}", flush=True)
        return self

    def __exit__(self, exc_type, *_):
        self._running = False
        if self._thread:
            self._thread.join()
        if _IS_TTY:
            icon = "✅" if exc_type is None else "❌"
            label = self._ok_msg if (exc_type is None and self._ok_msg) else self._msg
            sys.stdout.write(f"\r\033[K{icon} {label}\n")
            sys.stdout.flush()
        elif exc_type is None and self._ok_msg:
            print(f"  ✅ {self._ok_msg}", flush=True)

    def _spin(self) -> None:
        i = 0
        while self._running:
            frame = self._FRAMES[i % len(self._FRAMES)]
            sys.stdout.write(f"\r{frame} {self._msg}")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log_path(name: str) -> Path:
    return get_logs_dir() / name


def write_log(name: str, content: str) -> Path:
    path = log_path(name)
    path.write_text(content, encoding="utf-8")
    return path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def truncate(text: str, limit: int) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def load_claude_env() -> dict[str, str]:
    if not CLAUDE_SETTINGS_FILE.exists():
        return {}

    config = json.loads(CLAUDE_SETTINGS_FILE.read_text(encoding="utf-8"))
    env = config.get("env")
    if not isinstance(env, dict):
        return {}

    loaded: dict[str, str] = {}
    for key, value in env.items():
        if isinstance(key, str):
            loaded[key] = value if isinstance(value, str) else str(value)
    return loaded


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_claude_env())
    env.setdefault("TEAM_INFO_ROOT", str(REPO_ROOT))
    return env


def run_process(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    input_text: str | None = None,
    timeout: int = 900,
) -> tuple[int, str, str, bool]:
    proc = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdin=subprocess.PIPE if input_text is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    timed_out = False
    try:
        stdout, stderr = proc.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.terminate()
        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
    return proc.returncode or 0, stdout, stderr, timed_out


def _run_streaming(
    cmd: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    input_text: str | None = None,
    timeout: int = 900,
    on_stdout_line=None,
) -> tuple[int, str, str, bool]:
    """stdout を行単位でリアルタイム読み取りしながら実行する。on_stdout_line(line) で各行を受け取れる。"""
    proc = subprocess.Popen(
        cmd, cwd=str(cwd), env=env,
        stdin=subprocess.PIPE if input_text is not None else None,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, bufsize=1,
    )
    timed_out = False

    def _kill() -> None:
        nonlocal timed_out
        timed_out = True
        try:
            proc.terminate()
        except OSError:
            pass

    timer = threading.Timer(timeout, _kill)
    timer.start()

    if input_text is not None:
        try:
            proc.stdin.write(input_text)
            proc.stdin.close()
        except BrokenPipeError:
            pass

    stderr_buf: list[str] = []

    def _read_stderr() -> None:
        for ln in proc.stderr:
            stderr_buf.append(ln)

    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    stdout_parts: list[str] = []
    for ln in proc.stdout:
        stdout_parts.append(ln)
        if on_stdout_line:
            on_stdout_line(ln)

    stderr_thread.join(timeout=5)
    timer.cancel()
    proc.wait()

    return proc.returncode or 0, "".join(stdout_parts), "".join(stderr_buf), timed_out


def contains_token_limit(text: str) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in TOKEN_LIMIT_PATTERNS)


def fetch_bookmarks_payload(args, env: dict[str, str]) -> dict:
    cmd = [
        sys.executable,
        str(FETCH_BOOKMARKS_SCRIPT),
        "--account",
        args.account,
        "--count",
        str(args.count),
    ]
    if args.refresh_account_file:
        cmd.append("--refresh-account-file")

    code, stdout, stderr, timed_out = run_process(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        timeout=args.fetch_timeout,
    )
    write_log("fetch_bookmarks.stdout.log", stdout)
    write_log("fetch_bookmarks.stderr.log", stderr)

    if timed_out:
        raise JobError("fetch_bookmarks.py がタイムアウトしました")
    if code != 0:
        raise JobError(f"fetch_bookmarks.py が失敗しました: {stderr.strip() or stdout.strip()}")
    if not BOOKMARKS_FILE.exists():
        raise JobError(f"bookmarks_latest.json が見つかりません: {BOOKMARKS_FILE}")
    return load_json(BOOKMARKS_FILE)


def filter_new_bookmarks(bookmarks: list[dict], processed: set[str]) -> tuple[list[dict], list[dict]]:
    new_items: list[dict] = []
    skipped_existing: list[dict] = []

    for bookmark in bookmarks:
        tweet_id = str(bookmark.get("tweet_id") or "").strip()
        if not tweet_id:
            continue
        if tweet_id in processed:
            skipped_existing.append(bookmark)
            continue
        new_items.append(bookmark)

    return new_items, skipped_existing


def build_generation_prompt(
    *,
    agent_name: str,
    payload: dict,
    bookmarks: list[dict],
) -> str:
    account_profile = payload.get("account_profile", {})
    account_file_path = Path(account_profile.get("account_file_path") or "")
    account_text = account_file_path.read_text(encoding="utf-8") if account_file_path.exists() else ""

    prompt = f"""
あなたは team-info の X 投稿自動化ワーカーです。
目的は、Xブックマークから「ぐーたらAI社長」アカウント向けの下書きを生成し、構造化JSONだけを返すことです。

制約:
- 出力は JSON のみ。Markdown や説明文は禁止。
- 元ポストをコピペしない。型・視点・論点だけ借りる。
- アカウントのトンマナ・口調・NG事項を最優先で守る。
- 必要ならツリー形式にしてよい。各パーツは `parts` 配列に分ける。
- 各 draft に画像生成用の英語 prompt を1つ付ける。
- Claude fallback でも画像自体は生成しない。prompt と copy だけ返す。
- 不向きな bookmark は `skipped` に回す。

アカウントID: {payload.get("account")}
Xユーザー名: {payload.get("x_username")}
利用エージェント: {agent_name}

[account_profile]
{json.dumps(account_profile, ensure_ascii=False, indent=2)}

[account_file]
{account_text}

[new_bookmarks]
{json.dumps(bookmarks, ensure_ascii=False, indent=2)}

返す JSON の意味:
- `run_summary`: 今回の判断の短い要約
- `drafts[].memo`: 例 `from @author`
- `drafts[].rationale`: なぜこの型にしたかを1〜2文
- `drafts[].image_prompt.copy`: 画像に入れる短い日本語コピー
- `drafts[].image_prompt.prompt`: 英語プロンプト
- `skipped[].reason`: スキップ理由
""".strip()
    return prompt


def parse_json_output(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def run_codex(
    prompt: str,
    env: dict[str, str],
    timeout: int,
    *,
    on_progress=None,
    total: int = 0,
) -> tuple[dict | None, str]:
    codex_path = shutil.which("codex")
    if not codex_path:
        return None, "codex コマンドが見つかりません"

    output_path = get_logs_dir() / "codex_last_message.json"
    cmd = [
        codex_path,
        "exec",
        "-C",
        str(REPO_ROOT),
        "--sandbox",
        "read-only",
        "--color",
        "never",
        "--output-schema",
        str(SCHEMA_FILE),
        "-o",
        str(output_path),
        "-",
    ]

    draft_seen = 0

    def on_line(ln: str) -> None:
        nonlocal draft_seen
        count = ln.count('"bookmark_tweet_id"')
        if count and on_progress:
            draft_seen = min(draft_seen + count, total)
            on_progress(draft_seen, total)

    code, stdout, stderr, timed_out = _run_streaming(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        input_text=prompt,
        timeout=timeout,
        on_stdout_line=on_line,
    )
    write_log("codex.stdout.log", stdout)
    write_log("codex.stderr.log", stderr)

    combined = "\n".join([stdout, stderr]).strip()
    if timed_out:
        return None, "codex 実行がタイムアウトしたため終了しました"
    if contains_token_limit(combined):
        return None, f"codex token/context 制限: {truncate(combined, 400)}"
    if code != 0:
        return None, truncate(combined, 400) or f"codex 実行失敗 (exit={code})"

    raw = output_path.read_text(encoding="utf-8") if output_path.exists() else stdout
    try:
        return parse_json_output(raw), "ok"
    except json.JSONDecodeError as exc:
        return None, f"codex の JSON 解析に失敗しました: {exc}"


def run_claude(
    prompt: str,
    env: dict[str, str],
    timeout: int,
    *,
    on_progress=None,
    total: int = 0,
) -> tuple[dict, str]:
    claude_path = shutil.which("claude")
    if not claude_path:
        raise JobError("claude コマンドが見つかりません")

    schema_text = SCHEMA_FILE.read_text(encoding="utf-8")
    # stream-json で中間出力をリアルタイム受信し、draft の進捗をカウントする（--verbose 必須）
    cmd = [
        claude_path,
        "-p",
        "--verbose",
        "--permission-mode",
        "dontAsk",
        "--output-format",
        "stream-json",
        "--json-schema",
        schema_text,
        "--tools",
        "",
    ]

    accumulated_text = ""
    draft_seen = 0
    result_text = ""
    tool_use_input: dict | None = None  # --json-schema 使用時の構造化出力

    def on_line(ln: str) -> None:
        nonlocal accumulated_text, draft_seen, result_text, tool_use_input
        ln = ln.strip()
        if not ln:
            return
        try:
            event = json.loads(ln)
        except json.JSONDecodeError:
            return

        etype = event.get("type")

        # 最終結果を取り出す
        if etype == "result":
            result_text = event.get("result", "")
            return

        # assistant ブロックを処理
        if etype == "assistant":
            for block in event.get("message", {}).get("content", []):
                btype = block.get("type")
                if btype == "text":
                    # テキスト出力から draft 進捗をカウント
                    new_text = block.get("text", "")
                    new_part = new_text[len(accumulated_text):]
                    count = new_part.count('"bookmark_tweet_id"')
                    if count and on_progress:
                        draft_seen = min(draft_seen + count, total)
                        on_progress(draft_seen, total)
                    accumulated_text = new_text
                elif btype == "tool_use":
                    # --json-schema 使用時はここに構造化出力が入る
                    inp = block.get("input")
                    if isinstance(inp, dict):
                        tool_use_input = inp
                        count = str(inp).count('"bookmark_tweet_id"')
                        if count and on_progress:
                            on_progress(min(count, total), total)

    code, stdout, stderr, timed_out = _run_streaming(
        cmd,
        cwd=REPO_ROOT,
        env=env,
        input_text=prompt,
        timeout=timeout,
        on_stdout_line=on_line,
    )
    write_log("claude.stdout.log", stdout)
    write_log("claude.stderr.log", stderr)

    combined = "\n".join([stdout, stderr]).strip()
    if timed_out:
        raise JobError("claude 実行がタイムアウトしました")
    if code != 0:
        raise JobError(truncate(combined, 500) or f"claude 実行失敗 (exit={code})")

    # --json-schema 使用時は tool_use の input を優先して返す
    if tool_use_input is not None:
        return tool_use_input, "claude"

    # テキスト出力のフォールバック（--json-schema なし、または旧動作）
    output = result_text or accumulated_text or stdout
    try:
        return parse_json_output(output), "claude"
    except json.JSONDecodeError as exc:
        raise JobError(f"claude の JSON 解析に失敗しました: {exc}") from exc


def persist_generation(
    *,
    payload: dict,
    result: dict,
    agent_used: str,
) -> tuple[list[dict], set[str]]:
    handled_ids: set[str] = set()
    created: list[dict] = []
    preview_base = os.environ.get("X_PREVIEW_PUBLIC_URL", DEFAULT_PREVIEW_URL).rstrip("/")

    for item in result.get("drafts", []):
        tweet_id = str(item["bookmark_tweet_id"])
        author_username = item["author_username"]
        memo = item["memo"] or f"from @{author_username}"
        draft_id = save_draft(payload["account"], item["parts"], memo=memo)
        handled_ids.add(tweet_id)

        image_prompt = item.get("image_prompt", {})
        prompt_file = write_image_prompt_file(
            draft_id=draft_id,
            position=1,
            copy_text=image_prompt.get("copy", ""),
            prompt_text=image_prompt.get("prompt", ""),
            source_tweet_id=tweet_id,
        )

        preview_url = f"{preview_base}?draft={draft_id}"
        metadata = {
            "draft_id": draft_id,
            "account_id": payload["account"],
            "x_username": payload["x_username"],
            "source_agent": agent_used,
            "bookmark_tweet_id": tweet_id,
            "author_username": author_username,
            "memo": memo,
            "created_at": utc_now(),
            "preview_url": preview_url,
            "rationale": item.get("rationale", ""),
            "image_prompts": [
                {
                    "position": 1,
                    "copy": image_prompt.get("copy", ""),
                    "prompt": image_prompt.get("prompt", ""),
                    "file_path": str(prompt_file),
                }
            ],
        }
        metadata_path = save_draft_metadata(draft_id, metadata)

        created.append(
            {
                "draft_id": draft_id,
                "bookmark_tweet_id": tweet_id,
                "author_username": author_username,
                "memo": memo,
                "parts": item["parts"],
                "preview_url": preview_url,
                "image_prompt": metadata["image_prompts"][0],
                "metadata_path": str(metadata_path),
            }
        )

    for skipped in result.get("skipped", []):
        handled_ids.add(str(skipped["bookmark_tweet_id"]))

    return created, handled_ids


def send_discord_message(webhook_url: str, content: str) -> None:
    body = json.dumps({"content": content}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10):
        return


def send_discord_report(
    webhook_url: str,
    *,
    payload: dict,
    created: list[dict],
    skipped: list[dict],
    agent_used: str,
) -> None:
    header = (
        f"📝 X自動下書き作成完了\n"
        f"- account: @{payload['x_username']}\n"
        f"- source: {agent_used}\n"
        f"- created: {len(created)}\n"
        f"- skipped: {len(skipped)}\n"
        "- preview: start_preview.sh 起動中なら URL から確認可能"
    )
    send_discord_message(webhook_url, header)

    for draft in created:
        prompt = draft["image_prompt"]["prompt"]
        copy_text = draft["image_prompt"]["copy"]
        content = (
            f"**draft_id:** `{draft['draft_id']}`\n"
            f"**memo:** {draft['memo']}\n"
            f"**preview:** {draft['preview_url']}\n"
            f"**image prompt file:** `{draft['image_prompt']['file_path']}`\n\n"
            f"**本文プレビュー:**\n"
            f"```\n{truncate(draft['parts'][0], 700)}\n```\n"
            f"**画像コピー:** {truncate(copy_text, 120)}\n"
            f"**画像プロンプト:**\n"
            f"```\n{truncate(prompt, 900)}\n```"
        )
        send_discord_message(webhook_url, content)


def send_discord_error(webhook_url: str, message: str) -> None:
    send_discord_message(webhook_url, f"❌ X自動下書き作成エラー\n```\n{truncate(message, 1600)}\n```")


def main() -> int:
    parser = argparse.ArgumentParser(description="Xブックマーク定時下書き生成")
    parser.add_argument("--account", default="GUTARA")
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--codex-timeout", type=int, default=900)
    parser.add_argument("--claude-timeout", type=int, default=900)
    parser.add_argument("--fetch-timeout", type=int, default=120)
    parser.add_argument("--refresh-account-file", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    env = build_env()
    webhook_url = env.get(DISCORD_WEBHOOK_ENV, "").strip()

    print(f"\n📋 X 自動下書きパイプライン開始  (account={args.account})\n")

    try:
        # ── Step 1: ブックマーク取得 ──────────────────────────────
        with _Spinner(f"[1/4] ブックマーク取得中 (最大 {args.count} 件)...") as sp:
            payload = fetch_bookmarks_payload(args, env)
            total = len(payload.get("bookmarks", []))
            sp.finish_ok(f"[1/4] ブックマーク取得完了: {total} 件")

        processed = load_processed_bookmarks()
        new_bookmarks, already_done = filter_new_bookmarks(payload.get("bookmarks", []), processed)
        print(f"     🆕 新規: {len(new_bookmarks)} 件  /  ⏭ 既処理: {len(already_done)} 件")

        if not new_bookmarks:
            write_log(
                "scheduled_pipeline.log",
                f"{utc_now()} no new bookmarks. already_done={len(already_done)}\n",
            )
            print("\n📭 新規ブックマークはありませんでした。終了します。")
            return 0

        # ── Step 2: 下書き生成 ────────────────────────────────────
        prompt = build_generation_prompt(
            agent_name="codex",
            payload=payload,
            bookmarks=new_bookmarks,
        )

        result: dict | None = None
        agent_used = "codex"
        total_new = len(new_bookmarks)

        with _Spinner(f"[2/4] Codex で下書き生成中... 0/{total_new} 件") as sp:
            def _codex_progress(n: int, t: int) -> None:
                sp.update(f"[2/4] Codex で下書き生成中... {n}/{t} 件")

            result, codex_status = run_codex(
                prompt, env, args.codex_timeout,
                on_progress=_codex_progress, total=total_new,
            )
            if result is not None:
                sp.finish_ok(f"[2/4] Codex 生成完了: {len(result.get('drafts', []))}/{total_new} 件")

        if result is None:
            print(f"     ⚠️  Codex フォールバック: {truncate(codex_status, 100)}")
            write_log("codex_fallback_reason.log", codex_status + "\n")
            fallback_prompt = build_generation_prompt(
                agent_name="claude",
                payload=payload,
                bookmarks=new_bookmarks,
            )
            with _Spinner(f"[2/4] Claude で下書き生成中... 0/{total_new} 件") as sp:
                def _claude_progress(n: int, t: int) -> None:
                    sp.update(f"[2/4] Claude で下書き生成中... {n}/{t} 件")

                result, agent_used = run_claude(
                    fallback_prompt, env, args.claude_timeout,
                    on_progress=_claude_progress, total=total_new,
                )
                sp.finish_ok(f"[2/4] Claude 生成完了: {len(result.get('drafts', []))}/{total_new} 件")

        if args.dry_run:
            write_log(
                "scheduled_pipeline_dry_run.json",
                json.dumps(result, ensure_ascii=False, indent=2) + "\n",
            )
            print("\n🧪 dry-run 完了 (保存・通知はスキップ)")
            return 0

        # ── Step 3: 下書き保存 ────────────────────────────────────
        with _Spinner("[3/4] 下書き保存中...") as sp:
            created, handled_ids = persist_generation(
                payload=payload,
                result=result,
                agent_used=agent_used,
            )
            skipped_count = len(result.get("skipped", []))
            sp.finish_ok(f"[3/4] 保存完了: {len(created)} 件作成 / {skipped_count} 件スキップ")

        processed.update(handled_ids)
        save_processed_bookmarks(processed)

        for draft in created:
            print(f"     📝 {draft['draft_id']}  {draft['memo']}")
            print(f"        preview → {draft['preview_url']}")

        write_log(
            "scheduled_pipeline.log",
            (
                f"{utc_now()} created={len(created)} "
                f"skipped={skipped_count} "
                f"already_done={len(already_done)} source={agent_used}\n"
            ),
        )

        # ── Step 4: Discord 通知 ──────────────────────────────────
        if webhook_url and (created or result.get("skipped")):
            with _Spinner("[4/4] Discord へ通知中...") as sp:
                send_discord_report(
                    webhook_url,
                    payload=payload,
                    created=created,
                    skipped=result.get("skipped", []),
                    agent_used=agent_used,
                )
                sp.finish_ok("[4/4] Discord 通知完了")
        else:
            print("     💬 Discord Webhook 未設定のためスキップ")

        print(
            f"\n🎉 完了  created={len(created)}  skipped={skipped_count}  source={agent_used}\n"
        )
        return 0

    except Exception as exc:
        message = str(exc)
        write_log("scheduled_pipeline_error.log", f"{utc_now()} {message}\n")
        if webhook_url:
            try:
                send_discord_error(webhook_url, message)
            except Exception:
                pass
        print(f"\n❌ {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
