# X投稿自動化の launchd ジョブを render / install / uninstall するスクリプト。
# 3回/日の下書き生成と毎時のメトリクス収集を LaunchAgent として管理する。
# 使い方: python manage_launch_agents.py [render|install|uninstall|status]

from __future__ import annotations

import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

from runtime_store import get_config_root, get_logs_dir, get_runtime_root


REPO_ROOT = Path(__file__).resolve().parents[4]
SCRIPT_DIR = Path(__file__).parent
LAUNCH_AGENTS_DIR = Path.home() / "Library" / "LaunchAgents"
GUI_DOMAIN = f"gui/{os.getuid()}"
PLISTS = {
    "drafts": "com.team-info.x-draft-pipeline.plist",
    "metrics": "com.team-info.x-metrics-hourly.plist",
    "analysis": "com.team-info.x-daily-analysis.plist",
}


def build_draft_plist() -> dict:
    logs_dir = get_logs_dir()
    script = SCRIPT_DIR / "run_scheduled_draft_pipeline.sh"
    return {
        "Label": "com.team-info.x-draft-pipeline",
        "WorkingDirectory": str(REPO_ROOT),
        "ProgramArguments": ["/bin/bash", str(script)],
        "EnvironmentVariables": {
            "TEAM_INFO_ROOT": str(REPO_ROOT),
            "PYTHONUNBUFFERED": "1",
        },
        "StartCalendarInterval": [
            {"Hour": 0, "Minute": 0},
            {"Hour": 7, "Minute": 0},
            {"Hour": 12, "Minute": 0},
        ],
        "StandardOutPath": str(logs_dir / "launchd-draft-pipeline.out.log"),
        "StandardErrorPath": str(logs_dir / "launchd-draft-pipeline.err.log"),
    }


def build_metrics_plist() -> dict:
    logs_dir = get_logs_dir()
    script = SCRIPT_DIR / "run_metrics_collection.sh"
    return {
        "Label": "com.team-info.x-metrics-hourly",
        "WorkingDirectory": str(REPO_ROOT),
        "ProgramArguments": ["/bin/bash", str(script)],
        "EnvironmentVariables": {
            "TEAM_INFO_ROOT": str(REPO_ROOT),
            "PYTHONUNBUFFERED": "1",
        },
        "StartCalendarInterval": {"Minute": 5},
        "StandardOutPath": str(logs_dir / "launchd-metrics.out.log"),
        "StandardErrorPath": str(logs_dir / "launchd-metrics.err.log"),
    }


def build_analysis_plist() -> dict:
    logs_dir = get_logs_dir()
    script = SCRIPT_DIR / "run_daily_analysis.sh"
    return {
        "Label": "com.team-info.x-daily-analysis",
        "WorkingDirectory": str(REPO_ROOT),
        "ProgramArguments": ["/bin/bash", str(script)],
        "EnvironmentVariables": {
            "TEAM_INFO_ROOT": str(REPO_ROOT),
            "PYTHONUNBUFFERED": "1",
        },
        "StartCalendarInterval": {"Hour": 8, "Minute": 0},
        "StandardOutPath": str(logs_dir / "launchd-daily-analysis.out.log"),
        "StandardErrorPath": str(logs_dir / "launchd-daily-analysis.err.log"),
    }


def render_plists() -> list[Path]:
    rendered_dir = get_runtime_root() / "launchd-rendered"
    rendered_dir.mkdir(parents=True, exist_ok=True)

    mapping = {
        PLISTS["drafts"]: build_draft_plist(),
        PLISTS["metrics"]: build_metrics_plist(),
        PLISTS["analysis"]: build_analysis_plist(),
    }

    paths: list[Path] = []
    for name, payload in mapping.items():
        path = rendered_dir / name
        with path.open("wb") as f:
            plistlib.dump(payload, f, sort_keys=False)
        paths.append(path)
    return paths


def run_launchctl(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["launchctl", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def install() -> int:
    LAUNCH_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    get_logs_dir().mkdir(parents=True, exist_ok=True)
    rendered = render_plists()

    for path in rendered:
        target = LAUNCH_AGENTS_DIR / path.name
        target.write_bytes(path.read_bytes())
        run_launchctl("bootout", GUI_DOMAIN, str(target))
        completed = run_launchctl("bootstrap", GUI_DOMAIN, str(target))
        if completed.returncode != 0:
            print(completed.stderr.strip() or completed.stdout.strip(), file=sys.stderr)
            return completed.returncode

        with target.open("rb") as f:
            label = plistlib.load(f)["Label"]
        run_launchctl("kickstart", "-k", f"{GUI_DOMAIN}/{label}")
        print(f"✅ installed: {target}")
    return 0


def uninstall() -> int:
    for name in PLISTS.values():
        target = LAUNCH_AGENTS_DIR / name
        if not target.exists():
            continue
        run_launchctl("bootout", GUI_DOMAIN, str(target))
        target.unlink()
        print(f"🗑 removed: {target}")
    return 0


def status() -> int:
    for name in PLISTS.values():
        target = LAUNCH_AGENTS_DIR / name
        print(f"{name}: {'installed' if target.exists() else 'missing'}")
    print(f"logs: {get_config_root() / 'logs'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="X投稿自動化 LaunchAgents 管理")
    parser.add_argument("command", choices=["render", "install", "uninstall", "status"])
    args = parser.parse_args()

    if args.command == "render":
        for path in render_plists():
            print(path)
        return 0
    if args.command == "install":
        return install()
    if args.command == "uninstall":
        return uninstall()
    return status()


if __name__ == "__main__":
    raise SystemExit(main())
