#!/usr/bin/env bash
# 初回クローン後に一度だけ source して setup コマンドを有効化するファイル。
# 使い方: source ./bootstrap.sh  または  . ./bootstrap.sh
# このスクリプトは ~/.zshrc に自動チェック行も追記するため、
# 次回以降のターミナル起動時に Gemini / Codex でも自動でエイリアス登録が走る。

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

# ~/.zshrc / ~/.zprofile に自動チェック行を追記（Gemini / Codex 対応）
_SCRIPT="$_TEAM_INFO_BOOTSTRAP_ROOT/.agent/skills/common/scripts/register_aliases.py"
_MARKER="team-info alias auto-check"
for _RC in "$HOME/.zshrc" "$HOME/.zprofile" "$HOME/.bashrc" "$HOME/.bash_profile"; do
  [ -f "$_RC" ] || continue
  grep -qF "$_MARKER" "$_RC" && continue
  printf '\n# %s\n[ ! -f "$HOME/.config/team-info/aliases-registered" ] && [ -f "%s" ] && python "%s" --root "%s" 2>/dev/null\n' \
    "$_MARKER" "$_SCRIPT" "$_SCRIPT" "$_TEAM_INFO_BOOTSTRAP_ROOT" >> "$_RC"
done

echo "✅ setup コマンドが使えるようになりました"
echo "   → ターミナルで setup と入力してセットアップを開始してください"
echo "   （次回ターミナル起動時から Gemini / Codex でも自動登録が走ります）"
