#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path


CLAUDIAN_RELEASE_API = "https://api.github.com/repos/YishenTu/claudian/releases/latest"
CLAUDIAN_ASSETS = ("main.js", "manifest.json", "styles.css")
DEFAULT_AGENT_TEMPLATES = {
    "note-summarizer.md": """---
name: NoteSummarizer
description: Read attached notes and summarize them in Japanese with short, structured output.
model: sonnet
tools: [Read, Grep, Glob, LS]
---
You are a note summarizer for an Obsidian vault.

When invoked:
1. Read the attached note or the note explicitly mentioned by the user.
2. Summarize in Japanese.
3. Keep the response concise and structured.

Default response format:
- 3-line summary
- Key points
- Open questions or next actions

Do not edit files unless the user explicitly asks you to do so.
If the note context is missing, say what you need.
""",
    "file-organizer.md": """---
name: FileOrganizer
description: Inspect notes or folders, propose a clean organization plan in Japanese, and execute only after explicit approval.
model: sonnet
tools: [Read, Grep, Glob, LS, Bash, Write, Edit, MultiEdit]
---
You organize notes and folders in an Obsidian vault.

When invoked:
1. Inspect the specified folder, tags, or notes.
2. Explain the current issues in Japanese.
3. Propose a reorganization plan before making changes.
4. Wait for explicit user approval before editing, renaming, or moving files.

When preparing the plan, include:
- Current structure problems
- Proposed folders or naming rules
- Exact edits, renames, or moves you want to perform

After approval, execute carefully and report the changes you made.
""",
}


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def obsidian_json_path() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        return Path(appdata) / "obsidian" / "obsidian.json"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "obsidian" / "obsidian.json"
    xdg_config = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg_config) / "obsidian" / "obsidian.json"


def obsidian_app_exists() -> bool:
    if shutil.which("obsidian"):
        return True

    if sys.platform == "darwin":
        return Path("/Applications/Obsidian.app").exists()

    if sys.platform == "win32":
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Programs" / "Obsidian" / "Obsidian.exe",
            Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Obsidian" / "Obsidian.exe",
        ]
        return any(candidate.exists() for candidate in candidates)

    return False


def find_active_vault() -> Path:
    config_path = obsidian_json_path()
    data = load_json(config_path, {})
    vaults = data.get("vaults", {})
    if not isinstance(vaults, dict):
        raise RuntimeError(f"Invalid Obsidian vault metadata: {config_path}")

    fallback = None
    for value in vaults.values():
        if not isinstance(value, dict):
            continue
        path = value.get("path")
        if isinstance(path, str) and path:
            candidate = Path(path).expanduser()
            if fallback is None:
                fallback = candidate
            if value.get("open"):
                return candidate

    if fallback is not None:
        return fallback
    raise RuntimeError(f"No Obsidian vault was found in {config_path}")


def obsidian_cli_enabled() -> bool:
    data = load_json(obsidian_json_path(), {})
    return isinstance(data, dict) and bool(data.get("cli"))


def enable_obsidian_cli() -> None:
    config_path = obsidian_json_path()
    data = load_json(config_path, {})
    if not isinstance(data, dict):
        raise RuntimeError(f"Invalid Obsidian config: {config_path}")
    if data.get("cli") is True:
        return
    data["cli"] = True
    save_json(config_path, data)


def normalize_media_folder(raw_value: str | None) -> str:
    if not raw_value:
        return ""
    value = raw_value.strip()
    if value in {"", ".", "./", "/"}:
        return ""
    if value.startswith("./"):
        value = value[2:]
    return value.strip("/")


def read_attachment_folder(vault_path: Path) -> str:
    app_json = vault_path / ".obsidian" / "app.json"
    data = load_json(app_json, {})
    attachment_folder = ""
    if isinstance(data, dict):
        attachment_folder = data.get("attachmentFolderPath", "")
    return normalize_media_folder(attachment_folder)


def fetch_latest_claudian_release() -> dict:
    request = urllib.request.Request(
        CLAUDIAN_RELEASE_API,
        headers={"User-Agent": "team-info-obsidian-claudian"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def download_file(url: str, destination: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "team-info-obsidian-claudian"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def install_claudian_plugin(vault_path: Path) -> dict:
    release = fetch_latest_claudian_release()
    assets = {
        asset.get("name"): asset.get("browser_download_url")
        for asset in release.get("assets", [])
        if isinstance(asset, dict)
    }

    missing_assets = [name for name in CLAUDIAN_ASSETS if not assets.get(name)]
    if missing_assets:
        joined = ", ".join(missing_assets)
        raise RuntimeError(f"Claudian release assets are incomplete: {joined}")

    plugin_dir = vault_path / ".obsidian" / "plugins" / "claudian"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    for asset_name in CLAUDIAN_ASSETS:
        download_file(assets[asset_name], plugin_dir / asset_name)

    return {
        "plugin_dir": str(plugin_dir),
        "version": release.get("tag_name", ""),
    }


def enable_claudian_plugin(vault_path: Path) -> None:
    plugins_path = vault_path / ".obsidian" / "community-plugins.json"
    plugins = load_json(plugins_path, [])
    if not isinstance(plugins, list):
        plugins = []

    normalized = [item for item in plugins if isinstance(item, str)]
    if "claudian" not in normalized:
        normalized.append("claudian")
    save_json(plugins_path, normalized)


def update_claudian_settings(
    vault_path: Path,
    user_name: str | None,
    locale: str,
    permission_mode: str,
) -> Path:
    settings_path = vault_path / ".claude" / "claudian-settings.json"
    settings = load_json(settings_path, {})
    if not isinstance(settings, dict):
        settings = {}

    claude_cli_path = shutil.which("claude") or ""
    hostname = platform.node() or os.uname().nodename or "local"
    cli_paths = settings.get("claudeCliPathsByHost", {})
    if not isinstance(cli_paths, dict):
        cli_paths = {}
    if claude_cli_path:
        cli_paths[hostname] = claude_cli_path

    settings["locale"] = locale
    settings["permissionMode"] = permission_mode
    settings["loadUserClaudeSettings"] = True
    settings["mediaFolder"] = read_attachment_folder(vault_path)
    settings["claudeCliPathsByHost"] = cli_paths

    if user_name is not None:
        settings["userName"] = user_name

    save_json(settings_path, settings)
    return settings_path


def seed_default_agents(vault_path: Path) -> list[str]:
    agents_dir = vault_path / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    created: list[str] = []
    for file_name, content in DEFAULT_AGENT_TEMPLATES.items():
        destination = agents_dir / file_name
        if destination.exists():
            continue
        destination.write_text(content, encoding="utf-8")
        created.append(file_name)
    return created


def existing_default_agents(vault_path: Path) -> list[str]:
    agents_dir = vault_path / ".claude" / "agents"
    found: list[str] = []
    for file_name in DEFAULT_AGENT_TEMPLATES:
        if (agents_dir / file_name).exists():
            found.append(file_name)
    return found


def read_plugin_manifest(vault_path: Path) -> dict | None:
    manifest_path = vault_path / ".obsidian" / "plugins" / "claudian" / "manifest.json"
    if not manifest_path.exists():
        return None
    data = load_json(manifest_path, {})
    if isinstance(data, dict):
        return data
    return None


def build_doctor_status(vault_path: Path | None) -> dict:
    status = {
        "obsidian_app_exists": obsidian_app_exists(),
        "obsidian_cli_path": shutil.which("obsidian") or "",
        "obsidian_cli_enabled": obsidian_cli_enabled(),
        "claude_cli_path": shutil.which("claude") or "",
        "active_vault": str(vault_path) if vault_path else "",
    }

    if vault_path is None:
        return status

    settings_path = vault_path / ".claude" / "claudian-settings.json"
    manifest = read_plugin_manifest(vault_path)
    status.update(
        {
            "vault_attachment_folder": read_attachment_folder(vault_path),
            "claudian_plugin_installed": manifest is not None,
            "claudian_plugin_version": manifest.get("version", "") if manifest else "",
            "claudian_settings_exists": settings_path.exists(),
            "default_agents": existing_default_agents(vault_path),
        }
    )
    return status


def command_doctor(args: argparse.Namespace) -> int:
    vault_path = Path(args.vault).expanduser() if args.vault else None
    if vault_path is None:
        try:
            vault_path = find_active_vault()
        except RuntimeError:
            vault_path = None

    status = build_doctor_status(vault_path)
    json.dump(status, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def command_install(args: argparse.Namespace) -> int:
    enable_obsidian_cli()
    if args.vault:
        vault_path = Path(args.vault).expanduser()
    else:
        try:
            vault_path = find_active_vault()
        except RuntimeError:
            if args.skip_if_no_vault:
                summary = {
                    "skipped": "no_active_vault",
                    "obsidian_cli_path": shutil.which("obsidian") or "",
                    "obsidian_cli_enabled": obsidian_cli_enabled(),
                    "claude_cli_path": shutil.which("claude") or "",
                }
                json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
                sys.stdout.write("\n")
                return 0
            raise

    if not vault_path.exists():
        if args.skip_if_no_vault:
            summary = {
                "skipped": f"vault_not_found:{vault_path}",
                "obsidian_cli_path": shutil.which("obsidian") or "",
                "obsidian_cli_enabled": obsidian_cli_enabled(),
                "claude_cli_path": shutil.which("claude") or "",
            }
            json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
            return 0
        raise RuntimeError(f"Vault does not exist: {vault_path}")

    install_result = install_claudian_plugin(vault_path)
    enable_claudian_plugin(vault_path)
    settings_path = update_claudian_settings(
        vault_path=vault_path,
        user_name=args.user_name,
        locale=args.locale,
        permission_mode=args.permission_mode,
    )
    created_agents = seed_default_agents(vault_path)

    summary = {
        "vault": str(vault_path),
        "plugin_dir": install_result["plugin_dir"],
        "claudian_version": install_result["version"],
        "settings_path": str(settings_path),
        "created_default_agents": created_agents,
        "obsidian_cli_path": shutil.which("obsidian") or "",
        "obsidian_cli_enabled": obsidian_cli_enabled(),
        "claude_cli_path": shutil.which("claude") or "",
    }
    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="team-info helper for Obsidian CLI + Claudian")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="inspect Obsidian / Claudian status")
    doctor_parser.add_argument("--vault", help="override vault path")
    doctor_parser.set_defaults(func=command_doctor)

    install_parser = subparsers.add_parser("install", help="install Claudian into the active vault")
    install_parser.add_argument("--vault", help="override vault path")
    install_parser.add_argument("--user-name", default=os.environ.get("USER", ""), help="Claudian userName")
    install_parser.add_argument("--locale", default="ja", help="Claudian locale")
    install_parser.add_argument(
        "--permission-mode",
        choices=("normal", "plan", "yolo"),
        default="normal",
        help="initial Claudian permission mode",
    )
    install_parser.add_argument(
        "--skip-if-no-vault",
        action="store_true",
        help="exit successfully when no active vault exists yet",
    )
    install_parser.set_defaults(func=command_install)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except urllib.error.URLError as exc:
        print(f"Network error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
