#!/usr/bin/env python3
"""
vibe-local 導入支援スクリプト
落合陽一氏開発のローカルAIコーディングツール「vibe-local」のインストールをガイドします。

参考: https://weel.co.jp/media/tech/vibe-local/
"""

import sys
import platform
import subprocess
import shutil

# ===== 定数 =====
MIN_PYTHON = (3, 8)
INSTALL_URL_WIN = "https://raw.githubusercontent.com/ochyai/vibe-local/main/install.ps1"
INSTALL_URL_UNIX = "https://raw.githubusercontent.com/ochyai/vibe-local/main/install.sh"
REPO_URL = "https://github.com/ochyai/vibe-local"


def title(text: str) -> None:
    width = 60
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def ok(text: str) -> None:
    print(f"  [OK] {text}")


def warn(text: str) -> None:
    print(f"  [警告] {text}")


def info(text: str) -> None:
    print(f"  -> {text}")


def error(text: str) -> None:
    print(f"  [エラー] {text}")


# ===== チェック関数 =====

def check_python_version() -> bool:
    ver = sys.version_info[:2]
    if ver >= MIN_PYTHON:
        ok(f"Python {ver[0]}.{ver[1]} ✓ (3.8以上が必要)")
        return True
    else:
        error(f"Python {ver[0]}.{ver[1]} は古すぎます。3.8以上をインストールしてください。")
        return False


def check_ram() -> bool:
    """利用可能な物理メモリをGB単位で返してチェック"""
    try:
        import psutil
        total_gb = psutil.virtual_memory().total / (1024 ** 3)
        if total_gb >= 16:
            ok(f"RAM: {total_gb:.1f} GB ✓ (快適に動作します)")
        elif total_gb >= 8:
            warn(f"RAM: {total_gb:.1f} GB (最低要件8GB以上。16GB推奨)")
        else:
            error(f"RAM: {total_gb:.1f} GB — 8GB未満のため動作が保証されません")
            return False
        return True
    except ImportError:
        warn("psutil が未インストールのため RAM チェックをスキップします")
        info("手動確認: タスクマネージャー(Win) / アクティビティモニタ(Mac) でRAMを確認してください")
        return True


def check_vibe_local_installed() -> bool:
    return shutil.which("vibe-local") is not None


# ===== インストール関数 =====

def install_windows() -> None:
    title("vibe-local インストール (Windows)")
    print("""
  PowerShell を管理者権限で開き、以下を順番に実行してください:

  【ステップ1】実行ポリシーを変更
  -------------------------------------------------------
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
  -------------------------------------------------------

  【ステップ2】インストーラーを実行
  -------------------------------------------------------
  Invoke-Expression (Invoke-RestMethod -Uri {url})
  -------------------------------------------------------

  【ステップ3】PowerShell を再起動して起動確認
  -------------------------------------------------------
  vibe-local
  -------------------------------------------------------
""".format(url=INSTALL_URL_WIN))


def install_macos() -> None:
    title("vibe-local インストール (macOS)")
    print("""
  ターミナルで以下を実行してください:

  【ステップ1】インストーラーを実行
  -------------------------------------------------------
  curl -fsSL {url} | bash
  -------------------------------------------------------

  【ステップ2】ターミナルを再起動して起動確認
  -------------------------------------------------------
  vibe-local
  -------------------------------------------------------
""".format(url=INSTALL_URL_UNIX))


def install_linux() -> None:
    title("vibe-local インストール (Linux)")
    print("""
  ターミナルで以下を実行してください:

  【ステップ1】インストーラーを実行
  -------------------------------------------------------
  curl -fsSL {url} | bash
  -------------------------------------------------------

  【ステップ2】シェルを再起動して起動確認
  -------------------------------------------------------
  vibe-local
  -------------------------------------------------------
""".format(url=INSTALL_URL_UNIX))


# ===== 使い方ガイド =====

def usage_guide() -> None:
    title("vibe-local 使い方ガイド")
    print("""
  起動すると2つのモードを選択できます:
    1. 自動承認モード — AIが自律的にファイル変更を行います（効率重視）
    2. 通常モード     — ファイル変更のたびに許可を求めます（安全重視）

  日本語で指示できます。例:
    「Pythonでじゃんけんゲームを作って」
    「このフォルダにある画像を一覧表示するHTMLを作って」

  vibe-localの特徴:
    ✓ 完全オフライン — データがPC外に出ません
    ✓ 完全無料 / 商用利用可
    ✓ macOS / Windows / Linux 対応
    ✓ メモリ: 最低8GB（16GB推奨）
""")


# ===== メイン =====

def main() -> None:
    title("vibe-local 導入チェッカー")
    info(f"OS: {platform.system()} {platform.release()}")

    print("\n--- 環境チェック ---")
    py_ok = check_python_version()
    ram_ok = check_ram()

    if not py_ok:
        info(f"Python 3.8以上をインストール後に再実行してください: https://www.python.org/downloads/")
        sys.exit(1)

    print("\n--- vibe-local インストール状況 ---")
    if check_vibe_local_installed():
        ok("vibe-local はすでにインストール済みです！")
        usage_guide()
        return

    warn("vibe-local が見つかりません。インストール手順を表示します。")

    os_name = sys.platform
    if os_name == "win32":
        install_windows()
    elif os_name == "darwin":
        install_macos()
    else:
        install_linux()

    usage_guide()

    title("詳細情報")
    info(f"GitHub リポジトリ: {REPO_URL}")
    info("記事: https://weel.co.jp/media/tech/vibe-local/")
    print()


if __name__ == "__main__":
    main()
