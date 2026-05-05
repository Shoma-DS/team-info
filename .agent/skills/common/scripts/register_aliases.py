# チームツール用エイリアスをシェル設定に登録するスクリプト。
# Claude SessionStart hook / bootstrap.sh / ~/.zshrc の自動チェックから呼ばれ、
# 未登録の場合のみ書き込む（冪等）。引数でリポジトリルートを渡せる。
# macOS/Linux は ~/.config/team-info/env.sh、Windows は PowerShell プロファイルに追記する。

import json
import os
import pathlib
import platform
import sys

ALIASES = [
    ("setup",    'bash "{root}/setup/setup_mac.sh"'),
    ("x-post",   'bash "{root}/.agent/skills/x-post-writer/scripts/start_preview.sh"'),
    ("remotion", 'npm --prefix "{root}/Remotion/my-video" run dev'),
]

PS_FUNCTIONS = [
    ("setup",    '& "{root}\\setup\\setup_windows_safe.ps1"'),
    ("x-post",   'bash "{root}/.agent/skills/x-post-writer/scripts/start_preview.sh"'),
    ("remotion", 'npm --prefix "{root}/Remotion/my-video" run dev'),
]

MARKER = "alias x-post"
PS_MARKER = "function x-post"
REGISTERED_FLAG = pathlib.Path.home() / ".config" / "team-info" / "aliases-registered"

# ~/.zshrc に仕込む「ターミナル起動時の自動チェック行」のテンプレート
# TEAM_INFO_ROOT が未設定でも動くようにスクリプト絶対パスを直接埋め込む
_ZSHRC_HOOK_MARKER = "team-info alias auto-check"
_ZSHRC_HOOK_TMPL = (
    "\n# {marker}\n"
    "[ ! -f \"$HOME/.config/team-info/aliases-registered\" ]"
    " && [ -f \"{script}\" ]"
    " && python \"{script}\" --root \"{root}\" 2>/dev/null\n"
)


def _ensure_zshrc_hook(root: pathlib.Path, home: pathlib.Path) -> None:
    """~/.zshrc に自動チェック行を追加する（Gemini/Codex 向け）。"""
    script = root / ".agent" / "skills" / "common" / "scripts" / "register_aliases.py"
    for rc in [home / ".zshrc", home / ".zprofile", home / ".bashrc", home / ".bash_profile"]:
        if not rc.exists():
            continue
        content = rc.read_text(encoding="utf-8")
        if _ZSHRC_HOOK_MARKER in content:
            continue
        hook_line = _ZSHRC_HOOK_TMPL.format(
            marker=_ZSHRC_HOOK_MARKER,
            script=script,
            root=root,
        )
        with rc.open("a", encoding="utf-8") as f:
            f.write(hook_line)


def register_mac(root: pathlib.Path, home: pathlib.Path) -> bool:
    env_dir = home / ".config" / "team-info"
    env_file = env_dir / "env.sh"
    env_dir.mkdir(parents=True, exist_ok=True)

    existing = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    if MARKER in existing:
        return False

    # 古いエイリアス行を除去してから書き直す
    kept = [
        l for l in existing.splitlines()
        if not any(k in l for k in ("alias setup", "alias x-post", "alias remotion", "チームツール"))
    ]
    new_lines = [
        "",
        "# チームツール起動エイリアス (register_aliases.py により自動登録)",
    ]
    for name, cmd in ALIASES:
        new_lines.append(f"alias {name}='{cmd.format(root=root)}'")

    env_file.write_text("\n".join(kept + new_lines) + "\n", encoding="utf-8")

    # shell RC から env.sh を source する行を追加
    profile_line = f'[ -f "{env_file}" ] && source "{env_file}"'
    for rc in [home / ".zshrc", home / ".zprofile", home / ".bashrc", home / ".bash_profile"]:
        if not rc.exists():
            continue
        rc_content = rc.read_text(encoding="utf-8")
        if str(env_file) not in rc_content:
            with rc.open("a", encoding="utf-8") as f:
                f.write(f"\n{profile_line}\n")

    return True


def register_windows(root: pathlib.Path, home: pathlib.Path) -> bool:
    ps_profile_env = os.environ.get("PROFILE", "")
    profile = pathlib.Path(ps_profile_env) if ps_profile_env else (
        home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    )
    profile.parent.mkdir(parents=True, exist_ok=True)

    existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
    if PS_MARKER in existing:
        return False

    new_lines = [
        "",
        "# チームツール起動エイリアス (register_aliases.py により自動登録)",
    ]
    for name, cmd in PS_FUNCTIONS:
        new_lines.append(f'function {name} {{ {cmd.format(root=root)} }}')

    with profile.open("a", encoding="utf-8") as f:
        f.write("\n".join(new_lines) + "\n")

    return True


def main() -> None:
    # 登録済みマーカーがあればスキップ（初回のみ実行）
    if REGISTERED_FLAG.exists():
        sys.exit(0)

    # リポジトリルートの取得（引数 > CLAUDE_PROJECT_DIR の優先順）
    root_str = ""
    if len(sys.argv) >= 3 and sys.argv[1] == "--root":
        root_str = sys.argv[2]
    if not root_str:
        root_str = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if not root_str:
        sys.exit(0)

    root = pathlib.Path(root_str)
    home = pathlib.Path.home()

    if platform.system() == "Windows":
        registered = register_windows(root, home)
    else:
        registered = register_mac(root, home)
        # Gemini / Codex 向けに zshrc へ自動チェック行を仕込む
        _ensure_zshrc_hook(root, home)

    if registered:
        REGISTERED_FLAG.parent.mkdir(parents=True, exist_ok=True)
        REGISTERED_FLAG.touch()
        msg = "✅ エイリアス自動登録完了 (setup / x-post / remotion) — 新しいターミナルで使えます"
        print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    main()
