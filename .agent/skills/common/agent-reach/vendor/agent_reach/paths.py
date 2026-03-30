from __future__ import annotations

import os
import sys
from pathlib import Path


def _config_base() -> Path:
    override = os.environ.get("TEAM_INFO_AGENT_REACH_HOME")
    if override:
        return Path(override).expanduser()

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


def get_agent_reach_home() -> Path:
    return _config_base()


def get_config_dir() -> Path:
    return get_agent_reach_home()


def get_config_file() -> Path:
    return get_config_dir() / "config.yaml"


def get_tools_dir() -> Path:
    return get_agent_reach_home() / "tools"


def get_xiaoyuzhou_tools_dir() -> Path:
    return get_tools_dir() / "xiaoyuzhou"


def get_xhs_cookie_path() -> Path:
    return get_agent_reach_home() / "xhs-cookies.json"


def get_skill_source_path() -> Path | None:
    source = os.environ.get("TEAM_INFO_AGENT_REACH_SKILL_SOURCE")
    return Path(source).expanduser() if source else None


def get_skill_targets() -> list[Path]:
    explicit = os.environ.get("TEAM_INFO_AGENT_REACH_SKILL_TARGETS")
    if explicit:
        seen: set[Path] = set()
        targets: list[Path] = []
        for item in explicit.split(os.pathsep):
            if not item:
                continue
            candidate = Path(item).expanduser()
            if candidate in seen:
                continue
            seen.add(candidate)
            targets.append(candidate)
        if targets:
            return targets

    candidates: list[Path] = []

    openclaw_home = os.environ.get("OPENCLAW_HOME")
    if openclaw_home:
        candidates.append(Path(openclaw_home).expanduser() / ".openclaw" / "skills" / "agent-reach")

    candidates.extend(
        [
            Path.home() / ".openclaw" / "skills" / "agent-reach",
            Path.home() / ".claude" / "skills" / "agent-reach",
            Path.home() / ".agents" / "skills" / "agent-reach",
        ]
    )

    seen: set[Path] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        deduped.append(candidate)
    return deduped
