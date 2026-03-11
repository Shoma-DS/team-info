from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable


TEAM_INFO_ROOT_ENV = "TEAM_INFO_ROOT"
LOCAL_STATE_FILENAME = "local_state.json"
WORKED_BEFORE_FILENAME = "worked_before_machines.json"
LOCAL_STATE_APP_NAME = "team-info"
PYTHON_RUNTIME_IMAGE = "team-info/python-skill-runtime:3.11.9"
VOICEVOX_ENGINE_IMAGE = "voicevox/voicevox_engine"
VOICEVOX_ENGINE_CONTAINER = "team-info-voicevox-engine"
CONTAINER_REPO_ROOT = PurePosixPath("/workspace/team-info")
CONTAINER_SHARED_ROOT = PurePosixPath("/workspace/team-info-shared")
CONTAINER_HOME = PurePosixPath("/tmp/team-info-home")


def get_config_dir(app_name: str) -> Path:
    if sys.platform == "win32":
        base = Path(
            os.environ.get(
                "APPDATA",
                str(Path.home() / "AppData" / "Roaming"),
            )
        )
    else:
        base = Path(
            os.environ.get(
                "XDG_CONFIG_HOME",
                str(Path.home() / ".config"),
            )
        )
    return base / app_name


def get_local_state_path() -> Path:
    return get_config_dir(LOCAL_STATE_APP_NAME) / LOCAL_STATE_FILENAME


def get_worked_before_path() -> Path:
    return get_config_dir(LOCAL_STATE_APP_NAME) / WORKED_BEFORE_FILENAME


def _load_local_state() -> dict[str, str]:
    state_path = get_local_state_path()
    if not state_path.exists():
        return {}

    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(loaded, dict):
        return {}

    state: dict[str, str] = {}
    for key, value in loaded.items():
        if isinstance(key, str) and isinstance(value, str):
            state[key] = value
    return state


def _save_local_state(state: dict[str, str]) -> Path:
    state_path = get_local_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(state, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state_path


def _load_worked_before_state() -> dict[str, dict[str, str]]:
    state_path = get_worked_before_path()
    if not state_path.exists():
        return {}

    try:
        loaded = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(loaded, dict):
        return {}

    raw_machines = loaded.get("machines")
    if not isinstance(raw_machines, dict):
        return {}

    machines: dict[str, dict[str, str]] = {}
    for machine_id, entry in raw_machines.items():
        if not isinstance(machine_id, str):
            continue
        normalized: dict[str, str] = {}
        if isinstance(entry, dict):
            for key, value in entry.items():
                if isinstance(key, str) and isinstance(value, str):
                    normalized[key] = value
        machines[machine_id] = normalized
    return machines


def _save_worked_before_state(machines: dict[str, dict[str, str]]) -> Path:
    state_path = get_worked_before_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"machines": machines}
    state_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return state_path


def _normalize_path(path: Path) -> Path:
    expanded = path.expanduser()
    try:
        return expanded.resolve(strict=False)
    except OSError:
        return expanded.absolute()


def _looks_like_repo_root(path: Path) -> bool:
    return (path / ".agent" / "skills").is_dir() and (path / "AGENTS.md").is_file()


def _search_repo_root(start: Path) -> Path | None:
    candidate = _normalize_path(start)
    if candidate.is_file():
        candidate = candidate.parent

    for current in (candidate, *candidate.parents):
        if _looks_like_repo_root(current):
            return current
    return None


def _git_reported_repo_root(start: Path) -> Path | None:
    search_base = _normalize_path(start)
    if search_base.is_file():
        search_base = search_base.parent

    try:
        completed = subprocess.run(
            ["git", "-C", str(search_base), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None

    candidate = _normalize_path(Path(completed.stdout.strip()))
    if _looks_like_repo_root(candidate):
        return candidate
    return None


def get_saved_repo_root() -> Path | None:
    saved = _load_local_state().get("repo_root")
    if not saved:
        return None

    candidate = _normalize_path(Path(saved))
    if _looks_like_repo_root(candidate):
        return candidate
    return None


def save_repo_root(repo_root: str | Path | None = None) -> Path:
    if repo_root is None:
        candidate = get_repo_root()
    else:
        raw_path = Path(repo_root)
        if not raw_path.is_absolute():
            raw_path = Path.cwd() / raw_path
        candidate = _normalize_path(raw_path)

    if not _looks_like_repo_root(candidate):
        raise RuntimeError(f"Repository root was not found at: {candidate}")

    state = _load_local_state()
    state["repo_root"] = str(candidate)
    _save_local_state(state)
    return candidate


def get_repo_root() -> Path:
    env_override = os.environ.get(TEAM_INFO_ROOT_ENV)
    if env_override:
        env_path = _normalize_path(Path(env_override))
        if _looks_like_repo_root(env_path):
            return env_path

    saved_root = get_saved_repo_root()
    if saved_root is not None:
        return saved_root

    for resolver in (
        lambda: _search_repo_root(Path.cwd()),
        lambda: _git_reported_repo_root(Path.cwd()),
        lambda: _search_repo_root(Path(__file__)),
        lambda: _git_reported_repo_root(Path(__file__)),
    ):
        candidate = resolver()
        if candidate is not None:
            return candidate

    raise RuntimeError(
        "team-info repository root could not be detected. "
        f"Set {TEAM_INFO_ROOT_ENV} or run setup-local-machine once."
    )


def resolve_input_path(path_str: str) -> Path:
    candidate = Path(path_str).expanduser()
    if candidate.is_absolute():
        return candidate

    cwd_path = Path.cwd() / candidate
    if cwd_path.exists():
        return cwd_path.resolve()

    return (get_repo_root() / candidate).resolve()


def _bootstrap_python() -> Path:
    current = Path(sys.executable)
    if current.exists():
        return current

    for name in ("python3", "python", "py"):
        resolved = shutil.which(name)
        if resolved:
            return Path(resolved)

    raise RuntimeError("Python interpreter was not found.")


def _remotion_python_candidates() -> Iterable[Path]:
    repo_root = get_repo_root()
    remotion_root = repo_root / "Remotion" / ".venv"

    env_override = os.environ.get("REMOTION_PYTHON")
    if env_override:
        yield Path(env_override).expanduser()

    yield remotion_root / "Scripts" / "python.exe"
    yield remotion_root / "Scripts" / "python"
    yield remotion_root / "bin" / "python3"
    yield remotion_root / "bin" / "python"


def get_remotion_python() -> Path | None:
    for candidate in _remotion_python_candidates():
        if candidate.exists():
            return candidate.expanduser().absolute()
    return None


def ensure_remotion_venv() -> Path:
    existing = get_remotion_python()
    if existing is not None:
        return existing

    repo_root = get_repo_root()
    remotion_root = repo_root / "Remotion"
    venv_dir = remotion_root / ".venv"
    remotion_root.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [str(_bootstrap_python()), "-m", "venv", str(venv_dir)],
        check=True,
        cwd=str(repo_root),
    )

    created = get_remotion_python()
    if created is None:
        raise RuntimeError("Failed to create Remotion virtual environment.")
    return created


def get_python_runtime_mode() -> str:
    mode = os.environ.get("TEAM_INFO_PYTHON_RUNTIME", "docker").strip().lower()
    if mode not in {"docker", "host"}:
        raise RuntimeError(
            "TEAM_INFO_PYTHON_RUNTIME must be either 'docker' or 'host'."
        )
    return mode


def get_python_runtime_image() -> str:
    return os.environ.get("TEAM_INFO_PYTHON_IMAGE", PYTHON_RUNTIME_IMAGE)


def get_voicevox_engine_image() -> str:
    return os.environ.get("TEAM_INFO_VOICEVOX_IMAGE", VOICEVOX_ENGINE_IMAGE)


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    return _run_command(["docker", "version", "--format", "{{.Server.Version}}"]) is not None


def ensure_docker_available() -> None:
    if _docker_available():
        return
    raise RuntimeError(
        "Docker が必要です。Docker Desktop / Docker Engine を起動してから再実行してください。"
    )


def _docker_image_exists(image: str) -> bool:
    try:
        completed = subprocess.run(
            ["docker", "image", "inspect", image],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return completed.returncode == 0


def build_python_runtime_image() -> str:
    ensure_docker_available()

    repo_root = get_repo_root()
    dockerfile = repo_root / "docker" / "python-skill-runtime" / "Dockerfile"
    if not dockerfile.exists():
        raise RuntimeError(f"Dockerfile was not found: {dockerfile}")

    image = get_python_runtime_image()
    subprocess.run(
        ["docker", "build", "-t", image, "-f", str(dockerfile), str(repo_root)],
        check=True,
        cwd=str(repo_root),
    )
    return image


def ensure_python_runtime_image() -> str:
    image = get_python_runtime_image()
    if _docker_image_exists(image):
        return image
    return build_python_runtime_image()


def pull_voicevox_engine_image() -> str:
    ensure_docker_available()
    image = get_voicevox_engine_image()
    subprocess.run(["docker", "pull", image], check=True)
    return image


def _voicevox_container_name() -> str:
    return os.environ.get("TEAM_INFO_VOICEVOX_CONTAINER", VOICEVOX_ENGINE_CONTAINER)


def _container_exists(name: str) -> bool:
    output = _run_command(
        ["docker", "ps", "-a", "--filter", f"name=^{name}$", "--format", "{{.Names}}"]
    )
    return output == name


def is_voicevox_container_running() -> bool:
    name = _voicevox_container_name()
    output = _run_command(
        ["docker", "ps", "--filter", f"name=^{name}$", "--format", "{{.Names}}"]
    )
    return output == name


def get_voicevox_base_url(for_container: bool = False) -> str:
    base_url = (
        os.environ.get("VOICEVOX_API_BASE_URL")
        or os.environ.get("VOICEVOX_BASE")
        or "http://127.0.0.1:50021"
    )
    if not for_container:
        return base_url
    return re.sub(
        r"(?<=://)(?:127\.0\.0\.1|localhost)(?=[:/]|$)",
        "host.docker.internal",
        base_url,
        count=1,
    )


def is_voicevox_available(base_url: str | None = None, timeout: float = 2.0) -> bool:
    target_base = (base_url or get_voicevox_base_url()).rstrip("/")
    target = f"{target_base}/version"
    try:
        with urllib.request.urlopen(target, timeout=timeout) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, ValueError):
        return False


def start_voicevox_engine_container(wait_seconds: int = 60) -> str:
    ensure_docker_available()

    name = _voicevox_container_name()
    if is_voicevox_container_running():
        return name

    if _container_exists(name):
        subprocess.run(["docker", "start", name], check=True)
    else:
        subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                name,
                "-p",
                "50021:50021",
                get_voicevox_engine_image(),
            ],
            check=True,
        )

    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if is_voicevox_available():
            return name
        time.sleep(1)

    raise RuntimeError(
        "VOICEVOX Engine コンテナは起動しましたが、API の待受確認に失敗しました。"
    )


def stop_voicevox_engine_container() -> str:
    ensure_docker_available()

    name = _voicevox_container_name()
    if not _container_exists(name):
        return "not-found"
    if not is_voicevox_container_running():
        return "stopped"

    subprocess.run(["docker", "stop", name], check=True)
    return "stopped"


def _container_join(root: PurePosixPath, relative: Path) -> str:
    if not relative.parts:
        return str(root)
    return str(root.joinpath(*relative.parts))


def _rewrite_host_path_for_container(
    raw_value: str,
    host_root: Path,
    container_root: PurePosixPath,
) -> str | None:
    try:
        candidate = Path(raw_value).expanduser()
    except (TypeError, ValueError):
        return None

    if not candidate.is_absolute():
        return None

    normalized = _normalize_path(candidate)
    try:
        relative = normalized.relative_to(host_root)
    except ValueError:
        return None

    return _container_join(container_root, relative)


def _rewrite_argument_for_container(
    arg: str,
    repo_root: Path,
    shared_root: Path | None,
) -> str:
    if arg.startswith("--") and "=" in arg:
        key, value = arg.split("=", 1)
        rewritten_value = _rewrite_host_path_for_container(
            value, repo_root, CONTAINER_REPO_ROOT
        )
        if rewritten_value is not None:
            return f"{key}={rewritten_value}"
        if shared_root is not None:
            rewritten_value = _rewrite_host_path_for_container(
                value, shared_root, CONTAINER_SHARED_ROOT
            )
            if rewritten_value is not None:
                return f"{key}={rewritten_value}"
        return arg

    rewritten = _rewrite_host_path_for_container(arg, repo_root, CONTAINER_REPO_ROOT)
    if rewritten is not None:
        return rewritten

    if shared_root is not None:
        rewritten = _rewrite_host_path_for_container(
            arg, shared_root, CONTAINER_SHARED_ROOT
        )
        if rewritten is not None:
            return rewritten

    return arg


def _rewrite_run_args_for_container(run_args: list[str]) -> list[str]:
    repo_root = get_repo_root()
    shared_root = detect_shared_root()
    return [
        _rewrite_argument_for_container(arg, repo_root, shared_root)
        for arg in run_args
    ]


def _requires_voicevox_engine(run_args: list[str]) -> bool:
    if os.environ.get("TEAM_INFO_NEEDS_VOICEVOX") == "1":
        return True

    for arg in run_args:
        basename = Path(arg.split("=", 1)[-1]).name
        if basename in {"generate_voice.py", "generate_viral_voice.py"}:
            return True
    return False


def _pip_install_is_mutating(run_args: list[str]) -> bool:
    if len(run_args) < 3:
        return False
    return (
        run_args[0] == "-m"
        and run_args[1] == "pip"
        and run_args[2] in {"install", "uninstall"}
    )


def build_python_runtime_command(run_args: list[str]) -> list[str]:
    repo_root = get_repo_root()
    shared_root = detect_shared_root()
    runtime_image = ensure_python_runtime_image()
    config_dir = get_config_dir(LOCAL_STATE_APP_NAME)
    hf_cache_dir = Path.home() / ".cache" / "huggingface"

    command = ["docker", "run", "--rm"]
    if sys.stdin.isatty():
        command.append("-i")
    if sys.stdin.isatty() and sys.stdout.isatty():
        command.append("-t")

    if os.name != "nt" and hasattr(os, "getuid") and hasattr(os, "getgid"):
        command.extend(["--user", f"{os.getuid()}:{os.getgid()}"])

    if sys.platform not in {"darwin", "win32"}:
        command.extend(["--add-host", "host.docker.internal:host-gateway"])

    command.extend(
        [
            "-w",
            str(CONTAINER_REPO_ROOT),
            "-e",
            f"HOME={CONTAINER_HOME}",
            "-e",
            f"TEAM_INFO_ROOT={CONTAINER_REPO_ROOT}",
            "-e",
            "TEAM_INFO_IN_DOCKER=1",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            "MPLCONFIGDIR=/tmp/matplotlib",
            "-e",
            "NUMBA_CACHE_DIR=/tmp/numba-cache",
            "-e",
            "XDG_CACHE_HOME=/tmp/.cache",
            "-e",
            "XDG_CONFIG_HOME=/tmp/.config",
            "-e",
            f"VOICEVOX_API_BASE_URL={get_voicevox_base_url(for_container=True)}",
            "-e",
            f"VOICEVOX_BASE={get_voicevox_base_url(for_container=True)}",
            "-v",
            f"{repo_root}:{CONTAINER_REPO_ROOT}",
            "-v",
            f"{config_dir}:{CONTAINER_HOME}/.config/{LOCAL_STATE_APP_NAME}",
            "-v",
            f"{hf_cache_dir}:{CONTAINER_HOME}/.cache/huggingface",
        ]
    )

    if shared_root is not None:
        command.extend(
            [
                "-e",
                f"TEAM_INFO_SHARED_ROOT={CONTAINER_SHARED_ROOT}",
                "-v",
                f"{shared_root}:{CONTAINER_SHARED_ROOT}",
            ]
        )

    command.extend([runtime_image, "python", *_rewrite_run_args_for_container(run_args)])
    return command


def run_remotion_python(run_args: list[str]) -> subprocess.CompletedProcess[object]:
    if get_python_runtime_mode() == "host":
        remotion_python = ensure_remotion_venv()
        return subprocess.run([str(remotion_python), *run_args], cwd=str(get_repo_root()))

    if _pip_install_is_mutating(run_args):
        raise RuntimeError(
            "Docker ランタイムでは pip install / uninstall を直接保持できません。"
            " setup/requirements.txt を更新し、"
            " team_info_runtime.py build-remotion-python を実行してください。"
        )

    if (
        _requires_voicevox_engine(run_args)
        and os.environ.get("TEAM_INFO_AUTO_START_VOICEVOX", "1") != "0"
        and get_voicevox_base_url(for_container=True).startswith(
            "http://host.docker.internal:50021"
        )
    ):
        start_voicevox_engine_container()

    return subprocess.run(build_python_runtime_command(run_args), cwd=str(get_repo_root()))


def _run_command(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    if completed.returncode != 0:
        return None

    stdout = completed.stdout.strip()
    return stdout or None


def _macos_machine_marker() -> str | None:
    ioreg_output = _run_command(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"])
    if ioreg_output:
        match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', ioreg_output)
        if match:
            return match.group(1)

    system_profiler = _run_command(["system_profiler", "SPHardwareDataType"])
    if system_profiler:
        match = re.search(r"Hardware UUID:\s*([A-F0-9-]+)", system_profiler, re.I)
        if match:
            return match.group(1)
    return None


def _linux_machine_marker() -> str | None:
    for candidate in (Path("/etc/machine-id"), Path("/var/lib/dbus/machine-id")):
        if not candidate.exists():
            continue
        try:
            value = candidate.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if value:
            return value
    return None


def _windows_machine_marker() -> str | None:
    reg_output = _run_command(
        [
            "reg",
            "query",
            r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Cryptography",
            "/v",
            "MachineGuid",
        ]
    )
    if not reg_output:
        return None

    match = re.search(r"MachineGuid\s+REG_\w+\s+([^\s]+)", reg_output)
    if match:
        return match.group(1)
    return None


def get_machine_fingerprint() -> str:
    marker = os.environ.get("TEAM_INFO_MACHINE_ID")

    if not marker:
        if sys.platform == "darwin":
            marker = _macos_machine_marker()
        elif sys.platform == "win32":
            marker = _windows_machine_marker()
        else:
            marker = _linux_machine_marker()

    if not marker:
        marker = f"{platform.system()}|{platform.node()}|{uuid.getnode():012x}"

    return hashlib.sha256(marker.encode("utf-8")).hexdigest()


def get_saved_owner_machine_id() -> str | None:
    return _load_local_state().get("owner_machine_id")


def save_owner_machine(machine_id: str | None = None) -> str:
    owner_machine_id = machine_id or get_machine_fingerprint()
    state = _load_local_state()
    state["owner_machine_id"] = owner_machine_id
    _save_local_state(state)
    return owner_machine_id


def clear_owner_machine() -> None:
    state = _load_local_state()
    if "owner_machine_id" in state:
        del state["owner_machine_id"]
        _save_local_state(state)


def is_owner_machine() -> bool:
    expected = get_saved_owner_machine_id()
    if not expected:
        return False
    return expected == get_machine_fingerprint()


def has_worked_before(machine_id: str | None = None) -> bool:
    current_machine_id = machine_id or get_machine_fingerprint()
    machines = _load_worked_before_state()
    if current_machine_id in machines:
        return True

    legacy_state = _load_local_state()
    saved_repo_root = legacy_state.get("repo_root")
    saved_owner_machine_id = legacy_state.get("owner_machine_id")

    if saved_repo_root:
        return True

    if saved_owner_machine_id and saved_owner_machine_id == current_machine_id:
        return True

    return False


def mark_worked_before(machine_id: str | None = None) -> Path:
    current_machine_id = machine_id or get_machine_fingerprint()
    machines = _load_worked_before_state()
    now = datetime.now(timezone.utc).isoformat()
    entry = machines.get(current_machine_id, {})
    if "first_marked_at" not in entry:
        entry["first_marked_at"] = now
    entry["last_marked_at"] = now
    machines[current_machine_id] = entry
    return _save_worked_before_state(machines)


def clear_worked_before(machine_id: str | None = None) -> bool:
    current_machine_id = machine_id or get_machine_fingerprint()
    machines = _load_worked_before_state()
    if current_machine_id not in machines:
        return False
    del machines[current_machine_id]
    _save_worked_before_state(machines)
    return True


def _shared_root_candidates() -> Iterable[Path]:
    for env_name in ("TEAM_INFO_SHARED_ROOT", "TEAM_INFO_GDRIVE_ROOT"):
        env_value = os.environ.get(env_name)
        if env_value:
            yield Path(env_value).expanduser()

    home = Path.home()

    cloud_storage = home / "Library" / "CloudStorage"
    if cloud_storage.exists():
        for provider_root in cloud_storage.glob("GoogleDrive-*"):
            for drive_name in ("My Drive", "マイドライブ"):
                yield provider_root / drive_name / "team-info"
        for provider_root in cloud_storage.glob("OneDrive*"):
            yield provider_root / "team-info"

    for drive_name in ("My Drive", "マイドライブ"):
        yield home / "Google Drive" / drive_name / "team-info"
        yield home / "GoogleDrive" / drive_name / "team-info"

    yield home / "GoogleDrive" / "team-info"
    yield home / "OneDrive" / "team-info"

    for onedrive_root in home.glob("OneDrive*"):
        yield onedrive_root / "team-info"

    yield home / "Dropbox" / "team-info"


def detect_shared_root() -> Path | None:
    checked: set[Path] = set()
    for candidate in _shared_root_candidates():
        expanded = candidate.expanduser()
        try:
            resolved = expanded.resolve(strict=False)
        except OSError:
            resolved = expanded
        if resolved in checked:
            continue
        checked.add(resolved)
        if resolved.exists():
            return resolved
    return None
