#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
VENDOR_DIR = SKILL_DIR / "vendor"


def _default_home() -> Path:
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
    return base / "team-info" / "agent-reach"


def _venv_python(home: Path) -> Path:
    if sys.platform == "win32":
        return home / "venv" / "Scripts" / "python.exe"
    return home / "venv" / "bin" / "python"


def _venv_bin_dir(home: Path) -> Path:
    if sys.platform == "win32":
        return home / "venv" / "Scripts"
    return home / "venv" / "bin"


def _npm_prefix_dir(home: Path) -> Path:
    return home / "npm-global"


def _npm_bin_dir(home: Path) -> Path:
    prefix = _npm_prefix_dir(home)
    if sys.platform == "win32":
        return prefix
    return prefix / "bin"


def _skill_targets() -> str:
    targets = [
        str(Path.home() / ".openclaw" / "skills" / "agent-reach"),
        str(Path.home() / ".claude" / "skills" / "agent-reach"),
        str(Path.home() / ".agents" / "skills" / "agent-reach"),
    ]
    return os.pathsep.join(targets)


def _prepare_env() -> Path:
    home = Path(os.environ.get("TEAM_INFO_AGENT_REACH_HOME", _default_home())).expanduser()
    os.environ.setdefault("TEAM_INFO_AGENT_REACH_HOME", str(home))
    os.environ.setdefault(
        "TEAM_INFO_AGENT_REACH_SKILL_SOURCE",
        str(SKILL_DIR / "SKILL.md"),
    )
    os.environ.setdefault("TEAM_INFO_AGENT_REACH_SKILL_TARGETS", _skill_targets())
    npm_prefix = _npm_prefix_dir(home)
    npm_prefix.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("NPM_CONFIG_PREFIX", str(npm_prefix))
    os.environ.setdefault("npm_config_prefix", str(npm_prefix))
    path_prepend = [str(_venv_bin_dir(home)), str(_npm_bin_dir(home))]
    current_path = os.environ.get("PATH", "")
    if current_path:
        path_parts = current_path.split(os.pathsep)
        missing = [item for item in path_prepend if item not in path_parts]
        if missing:
            os.environ["PATH"] = os.pathsep.join([*missing, current_path])
    else:
        os.environ["PATH"] = os.pathsep.join(path_prepend)
    return home


def _auto_bootstrap(home: Path, missing: str) -> None:
    if os.environ.get("TEAM_INFO_AGENT_REACH_AUTO_BOOTSTRAP", "1") == "0":
        raise ModuleNotFoundError(missing)

    if os.environ.get("TEAM_INFO_AGENT_REACH_BOOTSTRAPPING") == "1":
        raise ModuleNotFoundError(missing)

    installer = SKILL_DIR / "scripts" / "install_team_info_agent_reach.py"
    env = os.environ.copy()
    env["TEAM_INFO_AGENT_REACH_HOME"] = str(home)
    env["TEAM_INFO_AGENT_REACH_BOOTSTRAPPING"] = "1"
    try:
        subprocess.run([sys.executable, str(installer)], check=True, env=env)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Agent Reach の初回 bootstrap に失敗しました。"
            f" 手動で `python \"{installer}\"` を実行して確認してください。"
            f" (exit: {exc.returncode})"
        ) from exc


def _maybe_reexec(home: Path) -> None:
    if os.environ.get("TEAM_INFO_AGENT_REACH_SKIP_REEXEC") == "1":
        return

    venv_python = _venv_python(home)
    if not venv_python.exists():
        return

    current = Path(sys.executable).resolve()
    if current == venv_python.resolve():
        return

    os.environ["TEAM_INFO_AGENT_REACH_SKIP_REEXEC"] = "1"
    os.execv(str(venv_python), [str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]])


def main() -> None:
    home = _prepare_env()
    _maybe_reexec(home)

    sys.path.insert(0, str(VENDOR_DIR))

    try:
        from agent_reach.cli import main as upstream_main
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependency"
        try:
            _auto_bootstrap(home, missing)
        except RuntimeError as bootstrap_error:
            print(str(bootstrap_error), file=sys.stderr)
            raise SystemExit(1) from exc
        except ModuleNotFoundError:
            print(
                "Agent Reach の依存がまだ入っていません。"
                f" 先に `python \"{SKILL_DIR / 'scripts' / 'install_team_info_agent_reach.py'}\"` を実行してください。"
                f" (missing: {missing})",
                file=sys.stderr,
            )
            raise SystemExit(1) from exc

        _maybe_reexec(home)
        from agent_reach.cli import main as upstream_main

    upstream_main()


if __name__ == "__main__":
    main()
