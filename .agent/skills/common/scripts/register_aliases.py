# チームツール用エイリアスをシェル設定に登録するスクリプト。
# setup / bootstrap から呼ばれ、不足しているエイリアスがある場合のみ書き込む（冪等）。
# 引数でリポジトリルートを渡せる。
# macOS/Linux は ~/.config/team-info/env.sh、Windows は PowerShell プロファイルに追記する。

import json
import os
import pathlib
import platform
import sys

ALIASES = [
    ("setup",    'bash "{root}/setup/setup_all.cmd"'),
    ("x-post",   'bash "{root}/.agent/skills/x-post-writer/scripts/start_preview.sh"'),
    ("remotion", 'npm --prefix "{root}/Remotion/my-video" run dev'),
    ("remodex",  'npx remodex'),
    ("renda",    'bash "{root}/Remotion/scripts/render_to_outputs.sh"'),
]

PS_FUNCTIONS = [
    ("setup",    '& "{root}\\setup\\setup_windows.ps1"'),
    ("x-post",   'bash "{root}/.agent/skills/x-post-writer/scripts/start_preview.sh"'),
    ("remotion", 'npm --prefix "{root}/Remotion/my-video" run dev'),
    ("remodex",  'npx remodex'),
    ("renda",    'bash "{root}/Remotion/scripts/render_to_outputs.sh"'),
]

REGISTERED_FLAG = pathlib.Path.home() / ".config" / "team-info" / "aliases-registered"


def register_mac(root: pathlib.Path, home: pathlib.Path) -> bool:
    env_dir = home / ".config" / "team-info"
    env_file = env_dir / "env.sh"
    env_dir.mkdir(parents=True, exist_ok=True)

    existing = env_file.read_text(encoding="utf-8") if env_file.exists() else ""

    # 古いエイリアス行を除去してから書き直す
    kept = [
        l for l in existing.splitlines()
        if not any(k in l for k in ("alias setup", "alias x-post", "alias remotion", "alias remodex", "alias renda", "チームツール"))
    ]
    while kept and not kept[-1].strip():
        kept.pop()
    new_lines = [
        "",
        "# チームツール起動エイリアス (register_aliases.py により自動登録)",
    ]
    for name, cmd in ALIASES:
        new_lines.append(f"alias {name}='{cmd.format(root=root)}'")

    new_content = "\n".join(kept + new_lines).strip() + "\n"
    changed = new_content != existing
    if changed:
        env_file.write_text(new_content, encoding="utf-8")

    # shell RC から env.sh を source する行を追加
    profile_line = f'[ -f "{env_file}" ] && source "{env_file}"'
    for rc in [home / ".zshrc", home / ".zprofile", home / ".bashrc", home / ".bash_profile"]:
        if not rc.exists():
            continue
        rc_content = rc.read_text(encoding="utf-8")
        if str(env_file) not in rc_content:
            with rc.open("a", encoding="utf-8") as f:
                f.write(f"\n{profile_line}\n")
            changed = True

    return changed


def register_windows(root: pathlib.Path, home: pathlib.Path) -> bool:
    ps_profile_env = os.environ.get("PROFILE", "")
    profile = pathlib.Path(ps_profile_env) if ps_profile_env else (
        home / "Documents" / "PowerShell" / "Microsoft.PowerShell_profile.ps1"
    )
    profile.parent.mkdir(parents=True, exist_ok=True)

    existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
    managed_names = {name for name, _ in PS_FUNCTIONS}
    kept = [
        line for line in existing.splitlines()
        if not any(line.strip().startswith(f"function {name}") for name in managed_names)
        and "チームツール起動エイリアス" not in line
    ]

    new_lines = [
        "",
        "# チームツール起動エイリアス (register_aliases.py により自動登録)",
    ]
    for name, cmd in PS_FUNCTIONS:
        new_lines.append(f'function {name} {{ {cmd.format(root=root)} }}')

    new_content = "\n".join(kept + new_lines).strip() + "\n"
    if new_content == existing:
        return False

    profile.write_text(new_content, encoding="utf-8")

    return True


def main() -> None:
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

    if registered:
        REGISTERED_FLAG.parent.mkdir(parents=True, exist_ok=True)
        REGISTERED_FLAG.touch()
        msg = "✅ エイリアス自動登録完了 (setup / x-post / remotion / remodex / renda) — 新しいターミナルで使えます"
        print(json.dumps({"systemMessage": msg}))


if __name__ == "__main__":
    main()
