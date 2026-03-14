#!/usr/bin/env python3
"""
Google Drive コピーツール
指定の Google Drive フォルダ（team-info）へファイル/フォルダをコピーする
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

GDRIVE_DEST = Path(
    "/Users/deguchishouma/Library/CloudStorage/"
    "GoogleDrive-syouma1674@gmail.com/マイドライブ/team-info"
)

TEAM_INFO_ROOT = Path("/Users/deguchishouma/team-info")


def list_path(path: Path, indent: int = 0) -> None:
    prefix = "  " * indent
    for item in sorted(path.iterdir()):
        kind = "/" if item.is_dir() else ""
        print(f"{prefix}{item.name}{kind}")


def pick_source() -> Path:
    """コピー元のパスをユーザーに選ばせる"""
    while True:
        raw = input("\nコピー元のパスを入力してください（絶対パス or team-info からの相対パス）:\n> ").strip()
        if not raw:
            continue
        p = Path(raw)
        if not p.is_absolute():
            p = TEAM_INFO_ROOT / p
        if p.exists():
            return p
        print(f"  ✗ パスが見つかりません: {p}")


def pick_files_from_dir(directory: Path) -> list[Path]:
    """ディレクトリ内のファイル一覧を表示し、番号で選ばせる"""
    items = sorted(directory.iterdir())
    print(f"\n{directory} 内のファイル/フォルダ:")
    for i, item in enumerate(items):
        kind = "[フォルダ]" if item.is_dir() else "[ファイル]"
        size = ""
        if item.is_file():
            size = f"  ({item.stat().st_size / 1024:.0f} KB)"
        print(f"  {i + 1:>3}. {kind} {item.name}{size}")

    print("\n番号を入力（複数はカンマ区切り、all で全選択）:")
    raw = input("> ").strip()

    if raw.lower() == "all":
        return items

    selected = []
    for token in raw.split(","):
        token = token.strip()
        if token.isdigit():
            idx = int(token) - 1
            if 0 <= idx < len(items):
                selected.append(items[idx])
            else:
                print(f"  ✗ 範囲外: {token}")
        else:
            print(f"  ✗ 無効な入力: {token}")
    return selected


def pick_dest_subdir() -> Path:
    """コピー先のサブフォルダを選ぶ（空のままで直接 team-info に置く）"""
    print(f"\nコピー先: {GDRIVE_DEST}")
    print("サブフォルダ名を入力（そのままコピーする場合は Enter）:")
    sub = input("> ").strip()
    if sub:
        return GDRIVE_DEST / sub
    return GDRIVE_DEST


def do_copy(src: Path, dest_dir: Path, dry_run: bool = False) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    if dry_run:
        print(f"  [DRY] {src} → {dest}")
        return

    print(f"  コピー中: {src.name} ...")
    if src.is_dir():
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        shutil.copy2(src, dest)
    print(f"  ✓ 完了: {dest}")


def notify(message: str) -> None:
    if sys.platform == "darwin":
        subprocess.run(
            ["osascript", "-e", f'display notification "{message}" with title "Google Drive コピー"'],
            check=False,
        )


def main() -> None:
    if not GDRIVE_DEST.exists():
        print(f"✗ Google Drive フォルダが見つかりません:\n  {GDRIVE_DEST}")
        print("Google Drive for Desktop が起動しているか確認してください。")
        sys.exit(1)

    print("=" * 50)
    print("  Google Drive コピーツール")
    print(f"  コピー先: マイドライブ/team-info")
    print("=" * 50)

    # コピーモード選択
    print("\nコピーモードを選択してください:")
    print("  1. フォルダごとコピー")
    print("  2. ファイル/フォルダを選んでコピー")
    while True:
        mode = input("> ").strip()
        if mode in ("1", "2"):
            break
        print("  1 か 2 を入力してください")

    # コピー元を決める
    src_path = pick_source()

    if mode == "1":
        # フォルダごとコピー
        if not src_path.is_dir():
            print(f"✗ フォルダではありません: {src_path}")
            sys.exit(1)
        targets = [src_path]
    else:
        # ファイル選択
        if src_path.is_dir():
            targets = pick_files_from_dir(src_path)
        else:
            targets = [src_path]

    if not targets:
        print("✗ 選択されたファイルがありません")
        sys.exit(1)

    # コピー先サブフォルダ
    dest_dir = pick_dest_subdir()

    # 確認
    print("\n--- コピー内容の確認 ---")
    for t in targets:
        kind = "[フォルダ]" if t.is_dir() else "[ファイル]"
        print(f"  {kind} {t}")
    print(f"→ {dest_dir}")
    print("\n実行しますか？ (y/n)")
    if input("> ").strip().lower() != "y":
        print("キャンセルしました")
        sys.exit(0)

    # 実行
    print()
    for t in targets:
        do_copy(t, dest_dir)

    notify(f"{len(targets)} 件を team-info にコピーしました")
    print(f"\n✓ 完了（{len(targets)} 件）")


if __name__ == "__main__":
    main()
