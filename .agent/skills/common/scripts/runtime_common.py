from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Iterable


TEAM_INFO_ROOT_ENV = "TEAM_INFO_ROOT"
LOCAL_STATE_FILENAME = "local_state.json"
LOCAL_STATE_APP_NAME = "team-info"


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
