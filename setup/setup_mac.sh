#!/usr/bin/env bash
# =============================================================================
# team-info セットアップスクリプト (macOS)
# =============================================================================
# 使い方:
#   bash /path/to/team-info/setup/setup_mac.sh
# =============================================================================

set -euo pipefail

# ── カラー出力 ──────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
step()    { echo -e "\n${BOLD}━━━ $* ━━━${RESET}"; }

# ── プロジェクトルート (repo root にいるならカレント優先、違えばスクリプト基準) ──
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

is_repo_root_dir() {
  local candidate="$1"
  [[ -f "$candidate/AGENTS.md" && -f "$candidate/setup/setup_all.cmd" ]]
}

CURRENT_DIR="$(pwd -P)"
if is_repo_root_dir "$CURRENT_DIR"; then
  TEAM_INFO_ROOT="$CURRENT_DIR"
else
  TEAM_INFO_ROOT="$SCRIPT_REPO_ROOT"
fi
NODE_VERSION="22.17.1"
PYTHON_VERSION="3.11.9"
DEFAULT_SHELL_NAME="$(basename "${SHELL:-zsh}")"
TEAM_INFO_ENV_DIR="$HOME/.config/team-info"
TEAM_INFO_ENV_FILE="$TEAM_INFO_ENV_DIR/env.sh"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
TEAM_INFO_LAUNCH_AGENT_PLIST="$LAUNCH_AGENTS_DIR/com.team-info.env.plist"
CODEX_NPM_PACKAGE="@openai/codex"

append_line_if_missing() {
  local file="$1"
  local line="$2"

  touch "$file"
  if ! grep -Fqx "$line" "$file"; then
    printf '%s\n' "$line" >> "$file"
  fi
}

get_shell_rc_files() {
  case "$DEFAULT_SHELL_NAME" in
    bash)
      printf '%s\n' "$HOME/.bash_profile" "$HOME/.bashrc"
      ;;
    zsh|*)
      printf '%s\n' "$HOME/.zprofile" "$HOME/.zshrc"
      ;;
  esac
}

append_line_to_shell_rcs() {
  local line="$1"
  local shell_rc
  while IFS= read -r shell_rc; do
    [[ -n "$shell_rc" ]] || continue
    append_line_if_missing "$shell_rc" "$line"
  done < <(get_shell_rc_files)
}

write_team_info_env_file() {
  mkdir -p "$TEAM_INFO_ENV_DIR"
  cat > "$TEAM_INFO_ENV_FILE" <<EOF
export TEAM_INFO_ROOT="$TEAM_INFO_ROOT"
EOF
}

ensure_shell_loads_team_info_env() {
  local shell_rc
  while IFS= read -r shell_rc; do
    [[ -n "$shell_rc" ]] || continue
    append_line_if_missing "$shell_rc" "[ -f \"$TEAM_INFO_ENV_FILE\" ] && source \"$TEAM_INFO_ENV_FILE\""
  done < <(get_shell_rc_files)
}

install_team_info_launch_agent() {
  local gui_domain
  mkdir -p "$LAUNCH_AGENTS_DIR"
  cat > "$TEAM_INFO_LAUNCH_AGENT_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.team-info.env</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/launchctl</string>
    <string>setenv</string>
    <string>TEAM_INFO_ROOT</string>
    <string>$TEAM_INFO_ROOT</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
</dict>
</plist>
EOF

  launchctl setenv TEAM_INFO_ROOT "$TEAM_INFO_ROOT" >/dev/null 2>&1 || return 1

  gui_domain="gui/$(id -u)"
  launchctl bootout "$gui_domain" "$TEAM_INFO_LAUNCH_AGENT_PLIST" >/dev/null 2>&1 || true
  launchctl bootstrap "$gui_domain" "$TEAM_INFO_LAUNCH_AGENT_PLIST" >/dev/null 2>&1 || return 1
  launchctl kickstart -k "$gui_domain/com.team-info.env" >/dev/null 2>&1 || true
}

get_python_user_bin() {
  local user_base
  user_base="$("$PYTHON311" -c 'import site; print(site.USER_BASE)')"
  printf '%s/bin\n' "$user_base"
}

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       team-info セットアップ (macOS)                 ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"
info "プロジェクトルート: $TEAM_INFO_ROOT"

# ── 1. Xcode Command Line Tools ───────────────────────────────────────────────
step "1. Xcode Command Line Tools"
if xcode-select -p &>/dev/null; then
  success "Xcode CLT インストール済み"
else
  warn "Xcode CLT が見つかりません。インストールを開始します..."
  xcode-select --install
  echo "  インストールダイアログが表示されたら完了後にこのスクリプトを再実行してください。"
  exit 0
fi

# ── 2. Homebrew ────────────────────────────────────────────────────────────────
step "2. Homebrew"
if command -v brew &>/dev/null; then
  success "Homebrew インストール済み: $(brew --version | head -1)"
else
  info "Homebrew をインストールします..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  # Apple Silicon の場合 PATH 追加
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
    append_line_if_missing "$HOME/.zprofile" 'eval "$(/opt/homebrew/bin/brew shellenv)"'
  fi
  success "Homebrew インストール完了"
fi

# ── 3. 基本ツール (brew) ───────────────────────────────────────────────────────
step "3. 基本ツール (git, git-lfs, gh)"
BREW_PACKAGES=(git git-lfs gh)
for pkg in "${BREW_PACKAGES[@]}"; do
  if brew list "$pkg" &>/dev/null; then
    success "$pkg インストール済み"
  else
    info "$pkg をインストールします..."
    brew install "$pkg"
    success "$pkg インストール完了"
  fi
done

if git lfs install --skip-repo &>/dev/null; then
  success "git lfs を初期化しました"
else
  warn "git lfs の初期化に失敗しました。必要なら手動で 'git lfs install --skip-repo' を実行してください。"
fi

# ── 4. GitHub アクセス & リポジトリ接続 ──────────────────────────────────────────
step "4. GitHub アクセス & リポジトリ接続"
warn "GitHub の招待メールを承認済みである必要があります。"
read -rp "  招待メールを承認済みですか？ 承認済みなら y を入力してください [y/N]: " confirmed
if [[ ! "$confirmed" =~ ^[Yy]$ ]]; then
  error "先に招待を承認してください。不明な場合は sho に確認してください。"
fi

if gh auth status &>/dev/null; then
  success "GitHub CLI (gh) 認証済み"
else
  info "GitHub CLI (gh) の認証を開始します。ブラウザでログインしてください..."
  gh auth login --web -h github.com -p https -w
  success "GitHub CLI (gh) 認証完了"
fi

info "リモートリポジトリの URL を設定します..."
git remote set-url origin https://github.com/Shoma-DS/team-info.git
success "リモート URL 設定完了: https://github.com/Shoma-DS/team-info.git"

# ── 5. pyenv + Python ─────────────────────────────────────────────────────────
step "5. pyenv + Python $PYTHON_VERSION"
if ! command -v pyenv &>/dev/null; then
  info "pyenv をインストールします..."
  brew install pyenv
  # shell 設定に追加
  append_line_to_shell_rcs '# pyenv'
  append_line_to_shell_rcs 'export PYENV_ROOT="$HOME/.pyenv"'
  append_line_to_shell_rcs 'export PATH="$PYENV_ROOT/bin:$PATH"'
  append_line_to_shell_rcs 'eval "$(pyenv init -)"'
  export PYENV_ROOT="$HOME/.pyenv"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)"
  success "pyenv インストール完了"
else
  success "pyenv インストール済み: $(pyenv --version)"
  export PYENV_ROOT="${PYENV_ROOT:-$HOME/.pyenv}"
  export PATH="$PYENV_ROOT/bin:$PATH"
  eval "$(pyenv init -)" 2>/dev/null || true
fi

# Python がなければインストール
if pyenv versions | grep -q "$PYTHON_VERSION"; then
  success "Python $PYTHON_VERSION インストール済み"
else
  info "Python $PYTHON_VERSION をインストールします（時間がかかります）..."
  pyenv install "$PYTHON_VERSION"
  success "Python $PYTHON_VERSION インストール完了"
fi

PYTHON311="$(pyenv root)/versions/$(pyenv versions --bare | grep "^$PYTHON_VERSION" | tail -1)/bin/python3"
[[ -x "$PYTHON311" ]] || error "Python $PYTHON_VERSION の実行ファイルが見つかりません: $PYTHON311"
info "Python: $PYTHON311 ($(${PYTHON311} --version))"

# ── 6. Python ランタイム方針 ───────────────────────────────────────────────
step "6. Python ランタイム方針"
success "Python 3.11 を使う土台を作りました"
warn "Remotion / Docker ランタイムや Python パッケージ群は、必要なスキルを初めて使うときに自動で準備する方針です。"

# ── 7. uv ─────────────────────────────────────────────────────────────────────
step "7. uv"
PYTHON_USER_BIN="$(get_python_user_bin)"
append_line_to_shell_rcs "export PATH=\"$PYTHON_USER_BIN:\$PATH\""
export PATH="$PYTHON_USER_BIN:$PATH"
if command -v uv &>/dev/null; then
  success "uv インストール済み: $(uv --version)"
else
  info "uv を入れます..."
  "$PYTHON311" -m pip install --user uv
  success "uv インストール完了"
fi

# ── 8. nvm + Node.js ──────────────────────────────────────────────────────────
step "8. nvm + Node.js $NODE_VERSION"
NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [[ ! -d "$NVM_DIR" ]]; then
  info "nvm をインストールします..."
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  success "nvm インストール完了"
fi

# nvm ロード
export NVM_DIR="$HOME/.nvm"
[[ -s "$NVM_DIR/nvm.sh" ]] && source "$NVM_DIR/nvm.sh"

if nvm ls "$NODE_VERSION" &>/dev/null; then
  success "Node.js $NODE_VERSION インストール済み"
else
  info "Node.js $NODE_VERSION をインストールします..."
  nvm install "$NODE_VERSION"
  success "Node.js $NODE_VERSION インストール完了"
fi

nvm use "$NODE_VERSION"
info "Node.js: $(node --version), npm: $(npm --version)"

# ── 9. Codex CLI ───────────────────────────────────────────────────────────────
step "9. Codex CLI"
if command -v codex &>/dev/null; then
  info "Codex CLI を更新します..."
else
  info "Codex CLI をグローバルに入れます..."
fi
if npm install -g "$CODEX_NPM_PACKAGE"; then
  success "Codex CLI インストール完了: $(codex --version 2>/dev/null || echo 'version unknown')"
else
  warn "Codex CLI のインストールに失敗しました。あとで npm install -g $CODEX_NPM_PACKAGE を実行してください。"
fi

# ── 10. TEAM_INFO_ROOT ─────────────────────────────────────────────────────────
step "10. TEAM_INFO_ROOT"
export TEAM_INFO_ROOT
write_team_info_env_file
ensure_shell_loads_team_info_env
if install_team_info_launch_agent; then
  success "TEAM_INFO_ROOT を launchctl に保存しました: $TEAM_INFO_ROOT"
else
  warn "launchctl への保存に失敗しました。ログイン後の GUI アプリで見えない場合があります。"
fi
if "$PYTHON311" "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" \
  setup-local-machine --repo-root "$TEAM_INFO_ROOT" --shell sh >/dev/null; then
  success "TEAM_INFO_ROOT を保存しました: $TEAM_INFO_ROOT"
else
  warn "TEAM_INFO_ROOT の保存に失敗しました。必要なら手動で設定してください。"
fi

# ── 11. 遅延セットアップの案内 ───────────────────────────────────────────────
step "11. 遅延セットアップの案内"
warn "以下は setup では入れません。必要なスキルを初めて使うタイミングで準備します。"
warn "  - Remotion / VOICEVOX / Docker runtime"
warn "  - Canva 補助や Dify 開発依存"
warn "  - Agent Reach / OpenClaw / Obsidian / Claudian"
warn "  - shared-agent-assets の同期処理"
warn "  - clone-website 用の Node 24 workspace 依存"

# ── 12. Docker (任意) ─────────────────────────────────────────────────────
step "12. Docker (任意)"
if command -v docker &>/dev/null; then
  success "Docker インストール済み: $(docker --version)"
  warn "Docker イメージの build / pull は重いため、必要なスキルの初回実行時に行います。"
else
  warn "Docker が見つかりません。"
  warn "→ https://www.docker.com/products/docker-desktop/ からインストールしてください。"
fi

# ── 13. セットアップ検証 ─────────────────────────────────────────────────────
VERIFY_STATUS=0
step "13. セットアップ検証"
VERIFY_SCRIPT="$SCRIPT_DIR/verify_setup.py"
if [[ -f "$VERIFY_SCRIPT" ]]; then
  if "$PYTHON311" "$VERIFY_SCRIPT" --repo-root "$TEAM_INFO_ROOT"; then
    success "セットアップ検証完了"
  else
    VERIFY_STATUS=$?
    warn "セットアップ検証で不足が見つかりました。ログを確認して不足分を埋めてください。"
  fi
else
  VERIFY_STATUS=1
  warn "検証スクリプトが見つかりません: $VERIFY_SCRIPT"
fi

# ── 完了 ──────────────────────────────────────────────────────────────────────
echo ""
if [[ "$VERIFY_STATUS" -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}"
  echo "╔══════════════════════════════════════════════════════╗"
  echo "║       セットアップ完了！                             ║"
  echo "╚══════════════════════════════════════════════════════╝"
  echo -e "${RESET}"
else
  echo -e "${YELLOW}${BOLD}"
  echo "╔══════════════════════════════════════════════════════╗"
  echo "║   セットアップは終わりましたが要確認箇所があります   ║"
  echo "╚══════════════════════════════════════════════════════╝"
  echo -e "${RESET}"
fi
echo "主要パス:"
echo "  Python:        $PYTHON311"
echo "  Node.js:       $(command -v node 2>/dev/null || echo '要: ターミナル再起動後に確認')"
echo "  Codex CLI:     $(command -v codex 2>/dev/null || echo '要: setup 再実行か手動インストール')"
echo "  プロジェクト:  $TEAM_INFO_ROOT"
echo "  TEAM_INFO_ENV: $TEAM_INFO_ENV_FILE"
echo "  検証結果:      $([[ "$VERIFY_STATUS" -eq 0 ]] && echo '成功' || echo '要確認')"
echo ""
echo "次のステップ:"
echo "  ・ターミナルを再起動して PATH を再読み込みしてください"
echo "  ・Remotion 系は初回実行時に Docker runtime を自動準備します"
echo "  ・Agent Reach は初回実行時に自動セットアップされます"
echo "  ・Claudian は必要になったら /claudian を実行してください"
echo "  ・Claude Code: code $TEAM_INFO_ROOT"
echo ""

exit "$VERIFY_STATUS"
