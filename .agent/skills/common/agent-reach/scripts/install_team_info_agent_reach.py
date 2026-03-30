#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import venv
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
WRAPPER = SKILL_DIR / "scripts" / "team_info_agent_reach.py"

BASE_PACKAGES = [
    "requests>=2.28",
    "feedparser>=6.0",
    "python-dotenv>=1.0",
    "loguru>=0.7",
    "pyyaml>=6.0",
    "rich>=13.0",
    "yt-dlp>=2024.0",
    "browser-cookie3>=0.19",
    "mcp[cli]>=1.0",
]


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


def main() -> int:
    home = Path(os.environ.get("TEAM_INFO_AGENT_REACH_HOME", _default_home())).expanduser()
    home.mkdir(parents=True, exist_ok=True)

    venv_dir = home / "venv"
    venv.create(venv_dir, with_pip=True, clear=False)

    python_bin = _venv_python(home)
    env = os.environ.copy()
    env["TEAM_INFO_AGENT_REACH_HOME"] = str(home)
    env["TEAM_INFO_AGENT_REACH_SKIP_REEXEC"] = "1"
    env.setdefault("TEAM_INFO_AGENT_REACH_SKILL_SOURCE", str(SKILL_DIR / "SKILL.md"))
    env.setdefault(
        "TEAM_INFO_AGENT_REACH_SKILL_TARGETS",
        os.pathsep.join(
            [
                str(Path.home() / ".openclaw" / "skills" / "agent-reach"),
                str(Path.home() / ".claude" / "skills" / "agent-reach"),
                str(Path.home() / ".agents" / "skills" / "agent-reach"),
            ]
        ),
    )

    subprocess.run(
        [str(python_bin), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
        check=True,
        env=env,
    )
    subprocess.run(
        [str(python_bin), "-m", "pip", "install", *BASE_PACKAGES],
        check=True,
        env=env,
    )

    install_args = sys.argv[1:] or ["install", "--env=auto"]
    subprocess.run([str(python_bin), str(WRAPPER), *install_args], check=True, env=env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
