#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()


COMMANDS: list[dict[str, str]] = [
    {
        "name": "team",
        "description": "チーム開発モードに切り替える",
        "kind": "mode",
    },
    {
        "name": "personal",
        "description": "個人開発モードに切り替える",
        "kind": "mode",
    },
    {
        "name": "c",
        "description": "コミットのみを行う",
        "kind": "git-commit-only",
    },
    {
        "name": "git",
        "description": "git-workflow に従ってコミットと push を行う",
        "kind": "skill",
        "skill_path": ".agent/skills/common/git-workflow/SKILL.md",
    },
    {
        "name": "pull",
        "description": "origin/main を fetch して pull --rebase する",
        "kind": "git-pull",
    },
    {
        "name": "setup",
        "description": "team-info の初回セットアップや再セットアップを始める",
        "kind": "skill",
        "skill_path": ".agent/skills/common/team-info-setup/SKILL.md",
    },
    {
        "name": "reach",
        "description": "Agent Reach スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/common/agent-reach/SKILL.md",
    },
    {
        "name": "tool-import",
        "description": "外部ツール取り込みスキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/common/repo-adapted-tool-import/SKILL.md",
    },
    {
        "name": "claudian",
        "description": "Obsidian / Claudian スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/common/obsidian-claudian/SKILL.md",
    },
    {
        "name": "shared-agent-assets",
        "description": "shared-agent-assets スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/common/shared-agent-assets/SKILL.md",
    },
    {
        "name": "clone-website",
        "description": "clone-website スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/web-design/clone-website/SKILL.md",
    },
    {
        "name": "acoriel",
        "description": "アコリエル動画制作スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/acoriel/remotion-template-acoriel-acoustic-cover/SKILL.md",
    },
    {
        "name": "sleep-travel",
        "description": "寝ながらトラベル動画制作スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/remotion/remotion-video-production/SKILL.md",
    },
    {
        "name": "lyric",
        "description": "歌詞演出マッピングスキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/remotion/lyric-emotion-mapper/SKILL.md",
    },
    {
        "name": "voice",
        "description": "VOICEVOX 音声生成スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/remotion/voice-script-launcher/SKILL.md",
    },
    {
        "name": "jmty",
        "description": "ジモティー投稿文スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/jmty/jmty-posts/SKILL.md",
    },
    {
        "name": "script",
        "description": "台本作成スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/remotion/script-writing-accounts-aware/SKILL.md",
    },
    {
        "name": "gdrive",
        "description": "Google Drive コピー系スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/common/gdrive-copy/SKILL.md",
    },
    {
        "name": "tyoudoii-illust-fetcher",
        "description": "tyoudoii-illust 取得スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/web-design/tyoudoii-illust-fetcher/SKILL.md",
    },
    {
        "name": "themeisle-illustration-fetcher",
        "description": "Themeisle illustration 取得スキルを起動する",
        "kind": "skill",
        "skill_path": ".agent/skills/web-design/themeisle-illustration-fetcher/SKILL.md",
    },
]


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def write_if_changed(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ensure_trailing_newline(content)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.write_text(content, encoding="utf-8")


def remove_if_exists(path: Path) -> None:
    if path.exists():
        path.unlink()


def shared_prompt_body(command: dict[str, str], placeholder: str) -> str:
    name = command["name"]
    kind = command["kind"]
    intro = [
        "この prompt / command は `team-info` リポジトリ専用です。",
        "まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。",
        "もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。",
        "このリポジトリでは `AGENTS.md` が正本です。",
        f"まず `AGENTS.md` を読み、`/{name}` のルールを確認してください。",
    ]

    if kind == "skill":
        skill_path = command["skill_path"]
        intro.append(
            f"次に `{skill_path}` を読み込み、そのスキルとして動作してください。"
        )
    elif kind == "git-commit-only":
        intro.append(
            "このコマンドはコミットのみです。push と PR 作成は行わないでください。"
        )
        intro.append(
            "コミットメッセージや Git の安全ルールは `.agent/skills/common/git-workflow/SKILL.md` に従ってください。"
        )
    elif kind == "git-pull":
        intro.append(
            "このコマンドは `origin/main` の取り込み専用です。`git fetch` のあと `pull --rebase` を行ってください。"
        )
    elif kind == "mode":
        intro.append(
            "開発モード管理は `AGENTS.md` のルールに従って `.dev-mode` を更新してください。"
        )
    else:
        raise ValueError(f"Unsupported kind: {kind}")

    intro.append(
        f"ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: {placeholder}"
    )
    return "\n".join(intro)


def gemini_command_content(command: dict[str, str]) -> str:
    body = shared_prompt_body(command, "{{args}}")
    return (
        f'description = "{command["description"]}"\n'
        'prompt = """\n'
        f"{body}\n"
        '"""\n'
    )


def codex_prompt_content(command: dict[str, str]) -> str:
    body = shared_prompt_body(command, "$ARGUMENTS")
    return (
        "---\n"
        f'description: "{command["description"]}"\n'
        'argument-hint: "[EXTRA=\\"free-form note\\"]"\n'
        "---\n\n"
        f"{body}\n"
    )


def gemini_settings_content() -> str:
    data = {
        "contextFileName": "AGENTS.md",
        "context": {
            "fileName": "AGENTS.md",
        },
        "fileFiltering": {
            "respectGitIgnore": True,
            "enableRecursiveFileSearch": True,
        },
    }
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def sync_repo_files() -> None:
    remove_if_exists(ROOT / "GEMINI.md")
    remove_if_exists(ROOT / "gemini.md")
    write_if_changed(ROOT / ".gemini" / "settings.json", gemini_settings_content())

    for command in COMMANDS:
        write_if_changed(
            ROOT / ".gemini" / "commands" / f'{command["name"]}.toml',
            gemini_command_content(command),
        )
        write_if_changed(
            ROOT / ".codex" / "prompts" / f'{command["name"]}.md',
            codex_prompt_content(command),
        )


def install_codex_prompts_to_home() -> list[Path]:
    installed: list[Path] = []
    target_dir = HOME / ".codex" / "prompts"
    target_dir.mkdir(parents=True, exist_ok=True)

    for command in COMMANDS:
        source = ROOT / ".codex" / "prompts" / f'{command["name"]}.md'
        target = target_dir / f'{command["name"]}.md'
        content = source.read_text(encoding="utf-8")
        write_if_changed(target, content)
        installed.append(target)
    return installed


def main() -> int:
    sync_repo_files()
    installed = install_codex_prompts_to_home()

    print("Synced Gemini project commands:")
    print(f"  {ROOT / '.gemini' / 'commands'}")
    print("Synced Codex prompt sources:")
    print(f"  {ROOT / '.codex' / 'prompts'}")
    print("Installed Codex prompts to:")
    for path in installed:
        print(f"  {path}")
    print("Restart Codex to load custom prompts. In Gemini CLI, run /commands reload if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
