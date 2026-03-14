#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


PYTHON_RUNTIME_IMAGE = "team-info/python-skill-runtime:3.11.9"
VOICEVOX_IMAGE = "voicevox/voicevox_engine:latest"
REQUIRED_HOST_COMMANDS = ("docker", "node", "npm", "codex")
HOST_IMPORTS = (
    "cv2",
    "numpy",
    "pytesseract",
    "faster_whisper",
    "pykakasi",
)
DOCKER_IMPORTS = (
    "cv2",
    "numpy",
    "PIL",
    "requests",
    "librosa",
    "pykakasi",
    "faster_whisper",
    "mediapipe",
    "soundfile",
    "jax",
)
REQUIRED_NODE_PROJECTS = (
    ("Remotion/my-video", "Remotion", "npm"),
    ("mcp-servers/voicevox", "VOICEVOX MCP", "npm"),
)
OPTIONAL_NODE_PROJECTS = (
    ("Remotion/scripts/canva_auth", "Canva auth helper", "npm"),
    ("docker/dify/web", "Dify Web", "pnpm"),
    ("docker/dify/sdks/nodejs-client", "Dify SDK", "pnpm"),
)


def _run(
    command: list[str],
    *,
    cwd: Path | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        check=check,
        capture_output=True,
        text=True,
    )


def _print_heading(title: str) -> None:
    print(f"\n== {title} ==")


def _truncate(text: str, limit: int = 240) -> str:
    compact = " ".join(text.strip().split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _check_host_commands(failures: list[str]) -> None:
    _print_heading("Host Commands")
    for command in REQUIRED_HOST_COMMANDS:
        path = shutil.which(command)
        if path:
            print(f"[OK] {command}: {path}")
        else:
            print(f"[NG] {command}: command not found")
            failures.append(f"{command} が見つかりません。")


def _check_git_lfs(failures: list[str]) -> None:
    _print_heading("Git LFS")
    if shutil.which("git") is None:
        print("[NG] git lfs: git command not found")
        failures.append("git が見つからないため git lfs を確認できません。")
        return

    completed = _run(["git", "lfs", "version"])
    if completed.returncode == 0:
        print(f"[OK] git lfs: {completed.stdout.strip()}")
        return

    message = _truncate(completed.stderr or completed.stdout or "git lfs version failed")
    print(f"[NG] git lfs: {message}")
    failures.append("git lfs が使えません。")


def _check_repo_git_hooks(repo_root: Path, failures: list[str]) -> None:
    _print_heading("Git Hooks")
    completed = _run(["git", "-C", str(repo_root), "config", "--get", "core.hooksPath"])
    hooks_path = completed.stdout.strip()
    if completed.returncode == 0 and hooks_path == ".githooks":
        print(f"[OK] core.hooksPath: {hooks_path}")
    else:
        print(f"[NG] core.hooksPath: {hooks_path or '(empty)'}")
        failures.append("Git hooks の置き場が .githooks に設定されていません。")

    pre_push = repo_root / ".githooks" / "pre-push"
    if pre_push.exists():
        print(f"[OK] pre-push hook: {pre_push}")
    else:
        print(f"[NG] pre-push hook: {pre_push}")
        failures.append("Git LFS 無料枠を守る pre-push hook が見つかりません。")


def _host_python_path(repo_root: Path) -> Path:
    candidates = [
        repo_root / "Remotion" / ".venv" / "bin" / "python",
        repo_root / "Remotion" / ".venv" / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("ホスト fallback 用の Python が見つかりません。")


def _run_import_check(python_path: Path, modules: tuple[str, ...]) -> dict[str, str]:
    code = (
        "import importlib, json\n"
        f"modules = {list(modules)!r}\n"
        "result = {}\n"
        "for module_name in modules:\n"
        "    try:\n"
        "        importlib.import_module(module_name)\n"
        "        result[module_name] = 'OK'\n"
        "    except Exception as exc:\n"
        "        result[module_name] = f'NG: {type(exc).__name__}: {exc}'\n"
        "print(json.dumps(result, ensure_ascii=False))\n"
    )
    completed = _run([str(python_path), "-c", code], check=True)
    return json.loads(completed.stdout)


def _check_host_python(repo_root: Path, failures: list[str]) -> None:
    _print_heading("Host Python Fallback")
    try:
        python_path = _host_python_path(repo_root)
    except FileNotFoundError as exc:
        print(f"[NG] {exc}")
        failures.append(str(exc))
        return

    print(f"[OK] python: {python_path}")
    try:
        results = _run_import_check(python_path, HOST_IMPORTS)
    except subprocess.CalledProcessError as exc:
        message = _truncate(exc.stderr or exc.stdout or str(exc))
        print(f"[NG] host import check failed: {message}")
        failures.append("ホスト fallback Python の import 確認に失敗しました。")
        return

    for module_name in HOST_IMPORTS:
        status = results.get(module_name, "NG: missing result")
        prefix = "[OK]" if status == "OK" else "[NG]"
        print(f"{prefix} {module_name}: {status}")
        if status != "OK":
            failures.append(f"ホスト fallback Python で {module_name} を import できません。")


def _runtime_script(repo_root: Path) -> Path:
    return repo_root / ".agent" / "skills" / "common" / "scripts" / "team_info_runtime.py"


def _check_docker_runtime(repo_root: Path, failures: list[str]) -> None:
    _print_heading("Docker Runtime")
    runtime_script = _runtime_script(repo_root)
    if shutil.which("docker") is None:
        print("[NG] docker: command not found")
        failures.append("docker が見つかりません。")
        return

    try:
        mode = _run([sys.executable, str(runtime_script), "python-runtime-mode"], check=True).stdout.strip()
    except subprocess.CalledProcessError as exc:
        message = _truncate(exc.stderr or exc.stdout or str(exc))
        print(f"[NG] python runtime mode check failed: {message}")
        failures.append("Python ランタイムモードの確認に失敗しました。")
        return
    print(f"[OK] python runtime mode: {mode}")
    if mode != "docker":
        failures.append("標準 Python ランタイムが docker ではありません。")

    image_check = _run(["docker", "image", "inspect", PYTHON_RUNTIME_IMAGE])
    if image_check.returncode == 0:
        print(f"[OK] runtime image: {PYTHON_RUNTIME_IMAGE}")
    else:
        print(f"[NG] runtime image: {PYTHON_RUNTIME_IMAGE}")
        failures.append("Python Docker ランタイムイメージがありません。")

    voicevox_check = _run(["docker", "image", "inspect", VOICEVOX_IMAGE])
    if voicevox_check.returncode == 0:
        print(f"[OK] voicevox image: {VOICEVOX_IMAGE}")
    else:
        print(f"[NG] voicevox image: {VOICEVOX_IMAGE}")
        failures.append("VOICEVOX Engine イメージがありません。")

    code = (
        "import importlib, json\n"
        f"modules = {list(DOCKER_IMPORTS)!r}\n"
        "result = {}\n"
        "for module_name in modules:\n"
        "    try:\n"
        "        importlib.import_module(module_name)\n"
        "        result[module_name] = 'OK'\n"
        "    except Exception as exc:\n"
        "        result[module_name] = f'NG: {type(exc).__name__}: {exc}'\n"
        "print(json.dumps(result, ensure_ascii=False))\n"
    )
    completed = _run(
        [
            sys.executable,
            str(runtime_script),
            "run-remotion-python",
            "--",
            "-c",
            code,
        ]
    )
    if completed.returncode != 0:
        message = _truncate(completed.stderr or completed.stdout or "docker import check failed")
        print(f"[NG] docker import check failed: {message}")
        failures.append("Docker ランタイム内の import 確認に失敗しました。")
        return

    results = json.loads(completed.stdout)
    for module_name in DOCKER_IMPORTS:
        status = results.get(module_name, "NG: missing result")
        prefix = "[OK]" if status == "OK" else "[NG]"
        print(f"{prefix} {module_name}: {status}")
        if status != "OK":
            failures.append(f"Docker ランタイムで {module_name} を import できません。")

    binary_code = (
        "import json, shutil\n"
        "binaries = ['ffmpeg', 'ffprobe', 'tesseract']\n"
        "print(json.dumps({name: shutil.which(name) for name in binaries}, ensure_ascii=False))\n"
    )
    try:
        binaries = _run(
            [
                sys.executable,
                str(runtime_script),
                "run-remotion-python",
                "--",
                "-c",
                binary_code,
            ],
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        message = _truncate(exc.stderr or exc.stdout or str(exc))
        print(f"[NG] docker binary check failed: {message}")
        failures.append("Docker ランタイム内のバイナリ確認に失敗しました。")
        return
    binary_paths = json.loads(binaries.stdout)
    for name in ("ffmpeg", "ffprobe", "tesseract"):
        path = binary_paths.get(name)
        if path:
            print(f"[OK] {name}: {path}")
        else:
            print(f"[NG] {name}: not found in Docker runtime")
            failures.append(f"Docker ランタイムで {name} が見つかりません。")

    try:
        tesseract_langs = _run(
            [
                sys.executable,
                str(runtime_script),
                "run-remotion-python",
                "--",
                "-c",
                (
                    "import subprocess\n"
                    "result = subprocess.run(['tesseract', '--list-langs'], capture_output=True, text=True, check=True)\n"
                    "print(result.stdout)\n"
                ),
            ],
            check=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        message = _truncate(exc.stderr or exc.stdout or str(exc))
        print(f"[NG] tesseract language check failed: {message}")
        failures.append("Docker ランタイム内の tesseract 言語確認に失敗しました。")
        return
    if "jpn" in tesseract_langs.split():
        print("[OK] tesseract lang: jpn")
    else:
        print("[NG] tesseract lang: jpn not found")
        failures.append("Docker ランタイムに tesseract の日本語辞書がありません。")


def _check_team_info_root(repo_root: Path, failures: list[str], warnings: list[str]) -> None:
    _print_heading("TEAM_INFO_ROOT")
    current = os.environ.get("TEAM_INFO_ROOT", "")
    if current == str(repo_root):
        print(f"[OK] current env: {current}")
    else:
        print(f"[NG] current env: {current or '(empty)'}")
        failures.append("現在のプロセスで TEAM_INFO_ROOT が正しく見えていません。")

    if sys.platform == "darwin":
        env_file = Path.home() / ".config" / "team-info" / "env.sh"
        expected = f'export TEAM_INFO_ROOT="{repo_root}"'
        if env_file.exists() and expected in env_file.read_text(encoding="utf-8"):
            print(f"[OK] env file: {env_file}")
        else:
            print(f"[NG] env file: {env_file}")
            failures.append("macOS の env.sh に TEAM_INFO_ROOT が保存されていません。")

        launchctl = _run(["launchctl", "getenv", "TEAM_INFO_ROOT"])
        launchctl_value = launchctl.stdout.strip()
        if launchctl.returncode == 0 and launchctl_value == str(repo_root):
            print(f"[OK] launchctl: {launchctl_value}")
        else:
            print(f"[NG] launchctl: {launchctl_value or '(empty)'}")
            failures.append("launchctl に TEAM_INFO_ROOT が正しく保存されていません。")
        return

    if sys.platform == "win32":
        ps = _run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "[System.Environment]::GetEnvironmentVariable('TEAM_INFO_ROOT','User')",
            ]
        )
        user_value = ps.stdout.strip()
        if ps.returncode == 0 and user_value == str(repo_root):
            print(f"[OK] user env: {user_value}")
        else:
            print(f"[NG] user env: {user_value or '(empty)'}")
            failures.append("Windows ユーザー環境変数に TEAM_INFO_ROOT が保存されていません。")
        return

    warnings.append("この OS の TEAM_INFO_ROOT 永続化チェックは未対応です。")


def _node_tool_command(tool: str) -> list[str] | None:
    if tool == "npm":
        return ["npm"] if shutil.which("npm") else None
    if tool == "pnpm":
        if shutil.which("pnpm"):
            return ["pnpm"]
        if shutil.which("corepack"):
            return ["corepack", "pnpm"]
        return None
    return [tool] if shutil.which(tool) else None


def _check_node_project(
    repo_root: Path,
    relative_path: str,
    label: str,
    tool: str,
    *,
    failures: list[str],
    warnings: list[str],
    required: bool,
) -> None:
    project_dir = repo_root / relative_path
    package_json = project_dir / "package.json"
    if not package_json.exists():
        if required:
            print(f"[NG] {label}: package.json not found ({project_dir})")
            failures.append(f"{label} の package.json が見つかりません。")
        else:
            print(f"[SKIP] {label}: not present")
        return

    tool_command = _node_tool_command(tool)
    if tool_command is None:
        message = f"{tool} command not found"
        print(f"[NG] {label}: {message}")
        if required:
            failures.append(f"{label} に必要な {tool} が見つかりません。")
        else:
            warnings.append(f"{label} の確認に必要な {tool} が見つかりません。")
        return

    command = [*tool_command, "ls", "--depth=0"] if tool == "npm" else [*tool_command, "list", "--depth", "0"]
    completed = _run(command, cwd=project_dir)
    if completed.returncode == 0:
        print(f"[OK] {label}: {tool} dependencies installed")
        return

    message = _truncate(completed.stderr or completed.stdout or "npm ls failed")
    print(f"[NG] {label}: {message}")
    if required:
        failures.append(f"{label} の npm 依存がそろっていません。")
    else:
        warnings.append(f"{label} の npm 依存確認で問題が出ました。")


def _check_node_projects(repo_root: Path, failures: list[str], warnings: list[str]) -> None:
    _print_heading("Node Projects")
    if shutil.which("npm") is None:
        print("[NG] npm: command not found")
        failures.append("npm が見つかりません。")
        return

    for relative_path, label, tool in REQUIRED_NODE_PROJECTS:
        _check_node_project(
            repo_root,
            relative_path,
            label,
            tool,
            failures=failures,
            warnings=warnings,
            required=True,
        )
    for relative_path, label, tool in OPTIONAL_NODE_PROJECTS:
        _check_node_project(
            repo_root,
            relative_path,
            label,
            tool,
            failures=failures,
            warnings=warnings,
            required=False,
        )


def _check_secret_template(repo_root: Path, warnings: list[str]) -> None:
    _print_heading("Secrets Template")
    credentials = Path.home() / ".secrets" / "canva_credentials.txt"
    if credentials.exists():
        print(f"[OK] Canva secrets template: {credentials}")
    else:
        print(f"[NG] Canva secrets template: {credentials}")
        warnings.append("Canva の鍵テンプレートがまだ作られていません。")


def main() -> int:
    parser = argparse.ArgumentParser(description="team-info setup verification")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="team-info repository root",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    failures: list[str] = []
    warnings: list[str] = []

    print("team-info setup verification")
    print(f"repo: {repo_root}")

    _check_host_commands(failures)
    _check_git_lfs(failures)
    _check_repo_git_hooks(repo_root, failures)
    _check_team_info_root(repo_root, failures, warnings)
    _check_host_python(repo_root, failures)
    _check_node_projects(repo_root, failures, warnings)
    _check_secret_template(repo_root, warnings)
    _check_docker_runtime(repo_root, failures)

    _print_heading("Summary")
    if failures:
        print("[NG] setup verification failed")
        for item in failures:
            print(f"  - {item}")
    else:
        print("[OK] setup verification passed")

    if warnings:
        print("Warnings:")
        for item in warnings:
            print(f"  - {item}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
