#!/usr/bin/env python3
"""
HyperFrames Studio preview をラップして Ask agent からローカルAI CLIを呼ぶ。
Studio shell へ overlay JS を注入し、Codex app-server / Claude Code CLI を
選択実行するためのローカルHTTP bridgeを提供する。
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import http.client
import json
import os
import select
import socket
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


PROJECT_DIR = Path(__file__).resolve().parents[1]
OVERLAY_PATH = PROJECT_DIR / "ask-agents-overlay.js"
DEFAULT_TARGET_HOST = "127.0.0.1"
DEFAULT_TARGET_PORT = 3002
DEFAULT_BRIDGE_PORT = 3102
DEFAULT_TIMEOUT_SECONDS = 30 * 60
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class ClientDisconnected(Exception):
    """Raised when the browser cancels a proxied response."""


@dataclass
class AgentJob:
    id: str
    providers: list[str]
    prompt: str
    cwd: str
    status: str = "pending"
    phase: str = "Queued"
    progress: int = 0
    current_provider: str | None = None
    provider_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    report: dict[str, Any] = field(default_factory=dict)
    logs: list[str] = field(default_factory=list)
    results: dict[str, dict[str, Any]] = field(default_factory=dict)
    provider_outputs: dict[str, list[str]] = field(default_factory=dict)
    error: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def log(self, message: str) -> None:
        line = f"{time.strftime('%H:%M:%S')} {message}"
        self.logs.append(line)
        self.logs = self.logs[-300:]
        self.updated_at = time.time()

    def set_progress(self, progress: int, phase: str | None = None) -> None:
        self.progress = max(0, min(100, int(progress)))
        if phase:
            self.phase = phase
        self.updated_at = time.time()

    def set_provider_state(self, provider: str, status: str, progress: int, detail: str = "") -> None:
        self.provider_states[provider] = {
            "status": status,
            "progress": max(0, min(100, int(progress))),
            "detail": detail,
            "updatedAt": time.time(),
        }
        self.current_provider = provider if status in {"running", "starting"} else self.current_provider
        if self.status == "running" and self.providers:
            total = max(1, len(self.providers))
            summed = sum(int(self.provider_states.get(item, {}).get("progress", 0)) for item in self.providers)
            provider_average = summed / total
            self.progress = max(self.progress, min(90, 8 + int(provider_average * 0.78)))
        self.updated_at = time.time()

    def capture_output(self, provider: str, text: str) -> None:
        if not text:
            return
        self.provider_outputs.setdefault(provider, []).append(text)
        self.provider_outputs[provider] = self.provider_outputs[provider][-120:]
        self.updated_at = time.time()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "providers": self.providers,
            "cwd": self.cwd,
            "status": self.status,
            "phase": self.phase,
            "progress": self.progress,
            "currentProvider": self.current_provider,
            "providerStates": self.provider_states,
            "logs": self.logs,
            "results": self.results,
            "report": self.report,
            "error": self.error,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }


JOBS: dict[str, AgentJob] = {}
JOBS_LOCK = threading.Lock()


def is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def is_disconnect_error(exc: BaseException) -> bool:
    if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
        return True
    if isinstance(exc, OSError):
        return exc.errno in {errno.EPIPE, errno.ECONNRESET, errno.ECONNABORTED}
    return False


def is_retryable_upstream_error(exc: BaseException) -> bool:
    if isinstance(exc, ClientDisconnected):
        return False
    return isinstance(
        exc,
        (
            BrokenPipeError,
            ConnectionResetError,
            TimeoutError,
            http.client.BadStatusLine,
            http.client.CannotSendRequest,
            http.client.IncompleteRead,
            http.client.RemoteDisconnected,
            http.client.ResponseNotReady,
            socket.timeout,
        ),
    )


def preview_serves_project(host: str, port: int, project_dir: Path) -> bool:
    connection = http.client.HTTPConnection(host, port, timeout=2)
    try:
        connection.request("GET", "/api/projects", headers={"Accept": "application/json"})
        response = connection.getresponse()
        if response.status != HTTPStatus.OK:
            return False
        payload = response.read(512 * 1024)
        body = json.loads(payload.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"[ask-agents] Existing server on {host}:{port} is not a compatible HyperFrames preview: {exc}")
        return False
    finally:
        connection.close()

    expected_dir = project_dir.resolve()
    for project in body.get("projects", []):
        try:
            candidate = Path(str(project.get("dir", ""))).resolve()
        except OSError:
            continue
        if candidate == expected_dir:
            return True
    return False


def find_available_port(host: str, preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 50):
        if not is_port_open(host, port):
            return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def json_dumps(data: Any) -> bytes:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def safe_read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or "0")
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    return json.loads(raw.decode("utf-8"))


def build_agent_prompt(prompt: str) -> str:
    return (
        "You are being invoked from HyperFrames Studio Ask agent.\n"
        "Make the requested targeted edit in the current HyperFrames project.\n"
        "Do not revert unrelated user changes. Keep Remotion files untouched unless explicitly requested.\n"
        "After editing, run a narrow validation command if it is quick and relevant.\n\n"
        f"{prompt.strip()}\n"
    )


def should_snapshot_path(path: Path) -> bool:
    ignored_parts = {
        "node_modules",
        "__pycache__",
        ".thumbnails",
        ".waveform-cache",
        "renders",
    }
    return not any(part in ignored_parts for part in path.parts)


def snapshot_project(cwd: str) -> dict[str, str]:
    root = Path(cwd)
    snapshot: dict[str, str] = {}
    for path in root.rglob("*"):
        if not should_snapshot_path(path.relative_to(root)):
            continue
        rel = path.relative_to(root).as_posix()
        try:
            if path.is_symlink():
                snapshot[rel] = f"symlink:{os.readlink(path)}"
            elif path.is_file():
                digest = hashlib.sha1(path.read_bytes()).hexdigest()
                snapshot[rel] = f"file:{digest}"
        except OSError:
            continue
    return snapshot


def diff_snapshots(before: dict[str, str], after: dict[str, str]) -> list[dict[str, str]]:
    paths = sorted(set(before) | set(after))
    changes: list[dict[str, str]] = []
    for path in paths:
        old = before.get(path)
        new = after.get(path)
        if old == new:
            continue
        if old is None:
            status = "added"
        elif new is None:
            status = "deleted"
        else:
            status = "modified"
        changes.append({"path": path, "status": status})
    return changes


def run_git(args: list[str], cwd: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", cwd, *args], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def build_report(job: AgentJob, before_snapshot: dict[str, str]) -> dict[str, Any]:
    changes = diff_snapshots(before_snapshot, snapshot_project(job.cwd))
    status = run_git(["status", "--short", "--", job.cwd], job.cwd)
    diff_stat = run_git(["diff", "--stat", "--", job.cwd], job.cwd)
    agent_notes: list[str] = []
    for provider in job.providers:
        output = "\n".join(job.provider_outputs.get(provider, [])).strip()
        if output:
            agent_notes.append(f"## {provider}\n{output[-2500:]}")
    if not agent_notes:
        if changes:
            agent_notes.append("エージェント実行は完了しました。変更ファイルは下の一覧で確認できます。")
        else:
            agent_notes.append("エージェント実行は完了しましたが、このプロジェクト内のファイル変更は検出されませんでした。")
    return {
        "summary": "\n\n".join(agent_notes),
        "changedFiles": changes,
        "gitStatus": status,
        "diffStat": diff_stat,
    }


class JsonRpcClient:
    def __init__(self, command: list[str], cwd: str, job: AgentJob, timeout: int) -> None:
        self.command = command
        self.cwd = cwd
        self.job = job
        self.timeout = timeout
        self.next_id = 1
        self.process: subprocess.Popen[str] | None = None

    def __enter__(self) -> "JsonRpcClient":
        self.process = subprocess.Popen(
            self.command,
            cwd=self.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
        )
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        if not self.process:
            return
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        self._write({"jsonrpc": "2.0", "method": method, **({"params": params} if params else {})})

    def request(self, method: str, params: dict[str, Any] | None = None) -> tuple[int, dict[str, Any]]:
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params or {}}
        self._write(payload)
        response = self.read_until_response(request_id)
        if "error" in response:
            raise RuntimeError(response["error"].get("message", json.dumps(response["error"])))
        return request_id, response.get("result", {})

    def _write(self, payload: dict[str, Any]) -> None:
        assert self.process and self.process.stdin
        self.process.stdin.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def read_until_response(self, request_id: int) -> dict[str, Any]:
        start = time.time()
        while time.time() - start < self.timeout:
            item = self._read_one()
            if item is None:
                continue
            if item.get("id") == request_id:
                return item
            self._handle_server_message(item)
        raise TimeoutError(f"Timed out waiting for JSON-RPC response id={request_id}")

    def read_until_turn_completed(self, thread_id: str) -> dict[str, Any]:
        start = time.time()
        final: dict[str, Any] = {}
        while time.time() - start < self.timeout:
            item = self._read_one()
            if item is None:
                continue
            self._handle_server_message(item)
            if item.get("method") == "turn/completed" and item.get("params", {}).get("threadId") == thread_id:
                final = item.get("params", {})
                break
        else:
            raise TimeoutError("Timed out waiting for Codex turn/completed")
        return final

    def _read_one(self) -> dict[str, Any] | None:
        assert self.process and self.process.stdout and self.process.stderr
        if self.process.poll() is not None:
            raise RuntimeError(f"Process exited with code {self.process.returncode}")
        readable, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], 0.25)
        for stream in readable:
            line = stream.readline()
            if not line:
                continue
            if stream is self.process.stderr:
                text = line.strip()
                if text:
                    self.job.log(f"codex stderr: {text[:500]}")
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                self.job.log(f"codex raw: {line.strip()[:500]}")
        return None

    def _handle_server_message(self, item: dict[str, Any]) -> None:
        method = item.get("method")
        params = item.get("params") or {}
        if method == "item/agentMessage/delta":
            delta = params.get("delta")
            if delta:
                self.job.capture_output("codex", delta)
                self.job.log(f"codex: {delta.strip()[:500]}")
        elif method == "turn/plan/updated":
            steps = params.get("plan") or []
            if steps:
                labels = [f"{s.get('status', '?')} {s.get('step', '')}" for s in steps[:6]]
                self.job.log("codex plan: " + " | ".join(labels))
                self.job.set_provider_state("codex", "running", 45, labels[0] if labels else "Planning")
        elif method == "turn/diff/updated":
            diff = params.get("diff") or ""
            self.job.log(f"codex diff updated ({len(diff)} chars)")
            self.job.set_provider_state("codex", "running", 72, "Applying file changes")
        elif method == "item/fileChange/patchUpdated":
            changes = params.get("changes") or []
            self.job.log(f"codex patch updated ({len(changes)} change(s))")
            self.job.set_provider_state("codex", "running", 78, f"{len(changes)} file change(s)")
        elif method == "error":
            error = params.get("error") or params
            self.job.log(f"codex error: {error}")
        elif "id" in item and method:
            self._respond_to_server_request(item)

    def _respond_to_server_request(self, item: dict[str, Any]) -> None:
        method = item.get("method")
        request_id = item.get("id")
        if request_id is None:
            return
        if method == "item/commandExecution/requestApproval":
            self._write({"jsonrpc": "2.0", "id": request_id, "result": {"decision": "decline"}})
            self.job.log("codex approval request declined by bridge")
        elif method == "item/fileChange/requestApproval":
            self._write({"jsonrpc": "2.0", "id": request_id, "result": {"decision": "decline"}})
            self.job.log("codex file approval request declined by bridge")
        elif method == "item/tool/requestUserInput":
            self._write({"jsonrpc": "2.0", "id": request_id, "result": {"answers": {}}})
            self.job.log("codex user-input request returned empty answers")
        elif method == "mcpServer/elicitation/request":
            self._write(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"action": "cancel", "content": None, "_meta": None},
                }
            )
            self.job.log("codex MCP elicitation cancelled by bridge")
        else:
            self._write(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32000, "message": f"Bridge cannot handle server request {method}"},
                }
            )
            self.job.log(f"codex unsupported server request: {method}")


def run_codex_app_server(prompt: str, cwd: str, job: AgentJob) -> dict[str, Any]:
    codex_bin = os.environ.get("ASK_AGENTS_CODEX_BIN", "codex")
    approval_policy = os.environ.get("ASK_AGENTS_CODEX_APPROVAL", "never")
    sandbox = os.environ.get("ASK_AGENTS_CODEX_SANDBOX", "workspace-write")
    model = os.environ.get("ASK_AGENTS_CODEX_MODEL")
    timeout = int(os.environ.get("ASK_AGENTS_CODEX_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS)))

    job.set_provider_state("codex", "starting", 5, "Starting Codex app-server")
    job.log("codex starting app-server")
    with JsonRpcClient([codex_bin, "app-server", "--listen", "stdio://"], cwd, job, timeout) as rpc:
        _, init_result = rpc.request(
            "initialize",
            {
                "clientInfo": {
                    "name": "hyperframes-ask-agents",
                    "title": "HyperFrames Ask Agents",
                    "version": "0.1.0",
                },
                "capabilities": {"experimentalApi": True},
            },
        )
        job.set_provider_state("codex", "running", 18, "Initialized app-server")
        job.log(f"codex initialized: {init_result.get('userAgent', 'ok')}")
        rpc.notify("initialized")

        thread_params: dict[str, Any] = {
            "cwd": cwd,
            "approvalPolicy": approval_policy,
            "sandbox": sandbox,
            "ephemeral": True,
        }
        if model:
            thread_params["model"] = model
        _, thread_result = rpc.request("thread/start", thread_params)
        thread = thread_result.get("thread", {})
        thread_id = thread.get("id")
        if not thread_id:
            raise RuntimeError("Codex thread/start did not return thread.id")
        job.set_provider_state("codex", "running", 32, "Thread started")
        job.log(f"codex thread started: {thread_id}")

        turn_params: dict[str, Any] = {
            "threadId": thread_id,
            "cwd": cwd,
            "approvalPolicy": approval_policy,
            "input": [{"type": "text", "text": build_agent_prompt(prompt), "text_elements": []}],
        }
        if model:
            turn_params["model"] = model
        rpc.request("turn/start", turn_params)
        job.set_provider_state("codex", "running", 42, "Agent is editing")
        job.log("codex turn started")
        final = rpc.read_until_turn_completed(thread_id)
        job.set_provider_state("codex", "succeeded", 100, "Completed")
        job.log("codex turn completed")
        return {"threadId": thread_id, "final": final}


def run_claude_cli(prompt: str, cwd: str, job: AgentJob) -> dict[str, Any]:
    claude_bin = os.environ.get("ASK_AGENTS_CLAUDE_BIN", "claude")
    permission_mode = os.environ.get("ASK_AGENTS_CLAUDE_PERMISSION_MODE", "acceptEdits")
    timeout = int(os.environ.get("ASK_AGENTS_CLAUDE_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS)))
    model = os.environ.get("ASK_AGENTS_CLAUDE_MODEL")
    command = [
        claude_bin,
        "-p",
        "--permission-mode",
        permission_mode,
        "--output-format",
        "text",
    ]
    if model:
        command.extend(["--model", model])
    command.append(build_agent_prompt(prompt))

    job.set_provider_state("claude", "starting", 5, "Starting Claude CLI")
    job.log(f"claude starting CLI ({permission_mode})")
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output: list[str] = []
    start = time.time()
    assert process.stdout
    while True:
        if time.time() - start > timeout:
            process.terminate()
            raise TimeoutError("Claude CLI timed out")
        line = process.stdout.readline()
        if line:
            clean = line.rstrip()
            output.append(clean)
            if clean:
                job.capture_output("claude", clean)
                job.set_provider_state("claude", "running", min(92, 20 + len(output) * 2), "Receiving output")
                job.log(f"claude: {clean[:500]}")
        elif process.poll() is not None:
            break
        else:
            time.sleep(0.1)
    code = process.wait()
    if code != 0:
        raise RuntimeError(f"Claude CLI exited with code {code}")
    job.set_provider_state("claude", "succeeded", 100, "Completed")
    job.log("claude completed")
    return {"exitCode": code, "output": "\n".join(output[-80:])}


def run_job(job_id: str) -> None:
    with JOBS_LOCK:
        job = JOBS[job_id]
        job.status = "running"
        job.set_progress(3, "Preparing")
        for provider in job.providers:
            job.set_provider_state(provider, "pending", 0, "Waiting")
        job.log("job started")

    ok = True
    before_snapshot = snapshot_project(job.cwd)
    total = max(1, len(job.providers))
    for index, provider in enumerate(job.providers):
        base_progress = 8 + int(index * 76 / total)
        end_progress = 8 + int((index + 1) * 76 / total)
        try:
            job.current_provider = provider
            job.set_progress(base_progress, f"Running {provider}")
            if provider == "codex":
                job.results[provider] = run_codex_app_server(job.prompt, job.cwd, job)
            elif provider == "claude":
                job.results[provider] = run_claude_cli(job.prompt, job.cwd, job)
            else:
                raise ValueError(f"Unknown provider: {provider}")
            job.set_provider_state(provider, "succeeded", 100, "Completed")
            job.set_progress(end_progress, f"{provider} completed")
        except Exception as exc:  # noqa: BLE001 - surfaced to local Studio UI
            ok = False
            job.error = str(exc)
            job.results[provider] = {"error": str(exc)}
            job.set_provider_state(provider, "failed", 100, str(exc))
            job.log(f"{provider} failed: {exc}")
            break

    job.status = "succeeded" if ok else "failed"
    job.set_progress(92, "Collecting results")
    job.report = build_report(job, before_snapshot)
    job.set_progress(100, "Ready to review" if ok else "Failed")
    job.log(f"job {job.status}")


class AskAgentsServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        target_host: str,
        target_port: int,
        project_dir: Path,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.target_host = target_host
        self.target_port = target_port
        self.project_dir = project_dir


class AskAgentsHandler(BaseHTTPRequestHandler):
    server: AskAgentsServer

    def log_message(self, fmt: str, *args: object) -> None:
        sys.stderr.write("[ask-agents] " + fmt % args + "\n")

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,PATCH,DELETE,OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/ask-agents-overlay.js":
            self.send_overlay()
        elif parsed.path == "/ask-agents/status":
            self.send_json(
                {
                    "ok": True,
                    "providers": {
                        "codex": bool(find_executable(os.environ.get("ASK_AGENTS_CODEX_BIN", "codex"))),
                        "claude": bool(find_executable(os.environ.get("ASK_AGENTS_CLAUDE_BIN", "claude"))),
                    },
                    "projectDir": str(self.server.project_dir),
                }
            )
        elif parsed.path == "/ask-agents/jobs":
            with JOBS_LOCK:
                self.send_json({"jobs": [job.to_dict() for job in JOBS.values()]})
        elif parsed.path.startswith("/ask-agents/jobs/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            with JOBS_LOCK:
                job = JOBS.get(job_id)
            if not job:
                self.send_json({"error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
            else:
                self.send_json(job.to_dict())
        else:
            self.proxy_request()

    def do_POST(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/ask-agents/run":
            self.handle_run()
        else:
            self.proxy_request()

    def do_PUT(self) -> None:
        self.proxy_request()

    def do_PATCH(self) -> None:
        self.proxy_request()

    def do_DELETE(self) -> None:
        self.proxy_request()

    def send_overlay(self) -> None:
        try:
            data = OVERLAY_PATH.read_bytes()
        except OSError as exc:
            self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/javascript; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def handle_run(self) -> None:
        try:
            body = safe_read_json(self)
        except Exception as exc:  # noqa: BLE001
            self.send_json({"error": f"Invalid JSON: {exc}"}, status=HTTPStatus.BAD_REQUEST)
            return
        prompt = str(body.get("prompt") or "").strip()
        providers = body.get("providers")
        if not prompt:
            self.send_json({"error": "prompt is required"}, status=HTTPStatus.BAD_REQUEST)
            return
        if not isinstance(providers, list):
            self.send_json({"error": "providers must be an array"}, status=HTTPStatus.BAD_REQUEST)
            return
        providers = [str(provider) for provider in providers if provider in {"codex", "claude"}]
        if not providers:
            self.send_json({"error": "Select at least one provider"}, status=HTTPStatus.BAD_REQUEST)
            return

        job_id = str(uuid.uuid4())
        cwd = str(self.server.project_dir)
        job = AgentJob(id=job_id, providers=providers, prompt=prompt, cwd=cwd)
        with JOBS_LOCK:
            JOBS[job_id] = job
        threading.Thread(target=run_job, args=(job_id,), daemon=True).start()
        self.send_json({"jobId": job_id})

    def send_json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
        raw = json_dumps(data)
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except OSError as exc:
            if is_disconnect_error(exc):
                print(f"[ask-agents] Client disconnected before JSON response finished: {self.path}")
                return
            raise

    def proxy_request(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length else None
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }
        headers["Host"] = f"{self.server.target_host}:{self.server.target_port}"
        headers["Accept-Encoding"] = "identity"
        max_attempts = 2 if self.command == "GET" else 1
        for attempt in range(max_attempts):
            try:
                self.proxy_request_once(body, headers)
                return
            except ClientDisconnected:
                print(f"[ask-agents] Client disconnected while proxying {self.path}")
                return
            except Exception as exc:  # noqa: BLE001
                if attempt + 1 < max_attempts and is_retryable_upstream_error(exc):
                    print(f"[ask-agents] Retrying proxied GET after upstream reset: {self.path} ({exc})")
                    time.sleep(0.15)
                    continue
                self.send_json({"error": f"Proxy error: {exc}"}, status=HTTPStatus.BAD_GATEWAY)
                return

    def proxy_request_once(self, body: bytes | None, headers: dict[str, str]) -> None:
        upstream = http.client.HTTPConnection(self.server.target_host, self.server.target_port, timeout=60)
        try:
            upstream.request(self.command, self.path, body=body, headers=headers)
            response = upstream.getresponse()
            content_type = response.getheader("Content-Type", "")
            if "text/event-stream" in content_type:
                self.stream_upstream(response)
                return
            data = response.read()
            if self.should_inject_overlay(content_type):
                data = inject_overlay(data)
                content_type = "text/html; charset=utf-8"
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                lower = key.lower()
                if lower in HOP_BY_HOP_HEADERS or lower == "content-length":
                    continue
                if lower == "content-type":
                    value = content_type
                self.send_header(key, value)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            try:
                self.end_headers()
                self.wfile.write(data)
            except OSError as exc:
                if is_disconnect_error(exc):
                    raise ClientDisconnected() from exc
                raise
        finally:
            upstream.close()

    def should_inject_overlay(self, content_type: str) -> bool:
        path = urlsplit(self.path).path
        if path.startswith(("/api/", "/assets/", "/icons/")) or path == "/favicon.svg":
            return False
        return "text/html" in content_type

    def stream_upstream(self, response: http.client.HTTPResponse) -> None:
        try:
            self.send_response(response.status, response.reason)
            for key, value in response.getheaders():
                if key.lower() in HOP_BY_HOP_HEADERS:
                    continue
                self.send_header(key, value)
            self.end_headers()
        except OSError as exc:
            if is_disconnect_error(exc):
                raise ClientDisconnected() from exc
            raise

        while True:
            try:
                chunk = response.read(4096)
            except (ConnectionResetError, BrokenPipeError, http.client.IncompleteRead, http.client.RemoteDisconnected) as exc:
                print(f"[ask-agents] Upstream event stream closed while proxying {self.path}: {exc}")
                return
            if not chunk:
                break
            try:
                self.wfile.write(chunk)
                self.wfile.flush()
            except OSError as exc:
                if is_disconnect_error(exc):
                    raise ClientDisconnected() from exc
                raise


def inject_overlay(data: bytes) -> bytes:
    html = data.decode("utf-8", errors="replace")
    marker = '<script src="/ask-agents-overlay.js"></script>'
    if marker in html:
        return data
    if "</body>" in html:
        html = html.replace("</body>", f"  {marker}\n</body>", 1)
    else:
        html += marker
    return html.encode("utf-8")


def find_executable(name: str) -> str | None:
    if os.path.isabs(name) and os.access(name, os.X_OK):
        return name
    for path in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(path) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def start_preview_if_needed(project_dir: Path, target_host: str, target_port: int) -> tuple[int, subprocess.Popen[str] | None]:
    if is_port_open(target_host, target_port):
        if preview_serves_project(target_host, target_port, project_dir):
            print(f"[ask-agents] Reusing existing HyperFrames preview on http://{target_host}:{target_port}")
            return target_port, None
        new_port = find_available_port(target_host, target_port + 1)
        print(
            f"[ask-agents] Port {target_port} is in use by another preview/server; "
            f"starting this project on {new_port}"
        )
        target_port = new_port

    hyperframes_bin = project_dir / "node_modules" / ".bin" / "hyperframes"
    command = [str(hyperframes_bin if hyperframes_bin.exists() else "hyperframes"), "preview", "--port", str(target_port)]
    print(f"[ask-agents] Starting HyperFrames preview: {' '.join(command)}")
    process = subprocess.Popen(
        command,
        cwd=str(project_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    threading.Thread(target=stream_child_output, args=(process,), daemon=True).start()

    for _ in range(80):
        if process.poll() is not None:
            raise RuntimeError(f"HyperFrames preview exited with code {process.returncode}")
        if is_port_open(target_host, target_port):
            return target_port, process
        time.sleep(0.25)
    raise TimeoutError("Timed out waiting for HyperFrames preview to start")


def stream_child_output(process: subprocess.Popen[str]) -> None:
    if not process.stdout:
        return
    for line in process.stdout:
        print("[hyperframes] " + line.rstrip())


def stop_preview_process(process: subprocess.Popen[str] | None) -> None:
    if not process or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except KeyboardInterrupt:
        try:
            process.wait(timeout=2)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            pass
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=2)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HyperFrames preview with Ask Agents overlay.")
    parser.add_argument("--target-host", default=DEFAULT_TARGET_HOST)
    parser.add_argument("--target-port", type=int, default=DEFAULT_TARGET_PORT)
    parser.add_argument("--bridge-host", default="127.0.0.1")
    parser.add_argument("--bridge-port", type=int, default=DEFAULT_BRIDGE_PORT)
    parser.add_argument("--no-preview", action="store_true", help="Do not start HyperFrames preview; proxy an existing server.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    preview_process: subprocess.Popen[str] | None = None
    target_port = args.target_port
    try:
        if not args.no_preview:
            target_port, preview_process = start_preview_if_needed(PROJECT_DIR, args.target_host, args.target_port)
        server = AskAgentsServer(
            (args.bridge_host, args.bridge_port),
            AskAgentsHandler,
            target_host=args.target_host,
            target_port=target_port,
            project_dir=PROJECT_DIR,
        )
        print(f"[ask-agents] Studio with Ask Agents: http://{args.bridge_host}:{args.bridge_port}")
        print("[ask-agents] Press Ctrl+C to stop")
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_preview_process(preview_process)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
