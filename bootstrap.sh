#!/usr/bin/env bash
# 初回クローン後に一度だけ source して setup コマンドを有効化するファイル。
# 使い方: source ./bootstrap.sh  または  . ./bootstrap.sh
# エイリアス本体は setup 実行時に登録する。ターミナル起動時の自動チェックは行わない。

_TEAM_INFO_BOOTSTRAP_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"

setup() {
  case "$(uname -s)" in
    Darwin|Linux)
      bash "$_TEAM_INFO_BOOTSTRAP_ROOT/setup/setup_all.cmd"
      ;;
    *)
      echo "Windows の場合は PowerShell で実行してください:"
      echo "  . \"$_TEAM_INFO_BOOTSTRAP_ROOT\\bootstrap.ps1\""
      ;;
  esac
}

echo "✅ setup コマンドが使えるようになりました"
echo "   → ターミナルで setup と入力してセットアップを開始してください"
