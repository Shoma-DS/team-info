from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def get_repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


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
