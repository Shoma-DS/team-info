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

# ── プロジェクトルート (このスクリプトの親ディレクトリ) ─────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEAM_INFO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$TEAM_INFO_ROOT/Remotion/.venv"
NODE_VERSION="22.17.1"
PYTHON_VERSION="3.11"

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
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
  fi
  success "Homebrew インストール完了"
fi

# ── 3. 基本ツール (brew) ───────────────────────────────────────────────────────
step "3. 基本ツール (git, wget, tesseract, ffmpeg)"
BREW_PACKAGES=(git wget tesseract ffmpeg)
for pkg in "${BREW_PACKAGES[@]}"; do
  if brew list "$pkg" &>/dev/null; then
    success "$pkg インストール済み"
  else
    info "$pkg をインストールします..."
    brew install "$pkg"
    success "$pkg インストール完了"
  fi
done

# ── 4. pyenv + Python 3.11 ────────────────────────────────────────────────────
step "4. pyenv + Python $PYTHON_VERSION"
if ! command -v pyenv &>/dev/null; then
  info "pyenv をインストールします..."
  brew install pyenv
  # shell 設定に追加
  SHELL_RC="$HOME/.zshrc"
  if [[ "$SHELL" == *"bash"* ]]; then SHELL_RC="$HOME/.bash_profile"; fi
  {
    echo ''
    echo '# pyenv'
    echo 'export PYENV_ROOT="$HOME/.pyenv"'
    echo 'export PATH="$PYENV_ROOT/bin:$PATH"'
    echo 'eval "$(pyenv init -)"'
  } >> "$SHELL_RC"
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

# Python 3.11 がなければインストール
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

# ── 5. Python venv ────────────────────────────────────────────────────────────
step "5. Python 仮想環境 ($VENV_DIR)"
if [[ -d "$VENV_DIR" ]]; then
  warn "既存の venv が見つかりました: $VENV_DIR"
  read -rp "  再作成しますか? (y/N): " ans
  if [[ "$ans" =~ ^[Yy]$ ]]; then
    rm -rf "$VENV_DIR"
    info "既存の venv を削除しました"
  fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
  info "venv を作成します..."
  "$PYTHON311" -m venv "$VENV_DIR"
  success "venv 作成完了"
fi

PIP="$VENV_DIR/bin/pip"
PYTHON="$VENV_DIR/bin/python"

# pip アップグレード
"$PIP" install --upgrade pip setuptools wheel -q
success "pip アップグレード完了"

# ── 6. Python パッケージ ──────────────────────────────────────────────────────
step "6. Python パッケージのインストール"
info "requirements.txt からインストールします..."
"$PIP" install -r "$SCRIPT_DIR/requirements.txt"
success "requirements.txt インストール完了"

# jax: Apple Silicon と Intel で異なる
info "jax/jaxlib をインストールします..."
ARCH="$(uname -m)"
if [[ "$ARCH" == "arm64" ]]; then
  info "Apple Silicon (arm64) → jax[metal] をインストール"
  "$PIP" install "jax[metal]==0.4.38" || warn "jax[metal] のインストールに失敗しました（スキップ）"
else
  info "Intel Mac → jax[cpu] をインストール"
  "$PIP" install "jax[cpu]==0.4.38" || warn "jax[cpu] のインストールに失敗しました（スキップ）"
fi
success "jax インストール完了"

# ── 7. nvm + Node.js ──────────────────────────────────────────────────────────
step "7. nvm + Node.js $NODE_VERSION"
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

# ── 8. npm パッケージ (Remotion) ──────────────────────────────────────────────
step "8. npm パッケージ (Remotion/my-video)"
REMOTION_DIR="$TEAM_INFO_ROOT/Remotion/my-video"
if [[ -d "$REMOTION_DIR" ]]; then
  info "npm install を実行します..."
  cd "$REMOTION_DIR"
  npm install
  success "npm install 完了"
else
  warn "Remotion/my-video が見つかりません: $REMOTION_DIR"
fi

# ── 9. MCP サーバー (VOICEVOX) ────────────────────────────────────────────────
step "9. npm パッケージ (mcp-servers/voicevox)"
VOICEVOX_MCP_DIR="$TEAM_INFO_ROOT/mcp-servers/voicevox"
if [[ -d "$VOICEVOX_MCP_DIR" ]]; then
  cd "$VOICEVOX_MCP_DIR"
  npm install
  success "voicevox MCP npm install 完了"
fi

# ── 10. Docker 確認 ───────────────────────────────────────────────────────────
step "10. Docker"
if command -v docker &>/dev/null; then
  success "Docker インストール済み: $(docker --version)"
else
  warn "Docker が見つかりません。"
  warn "→ https://www.docker.com/products/docker-desktop/ からインストールしてください。"
fi

# ── 完了 ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║       セットアップ完了！                             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo "主要パス:"
echo "  Python venv:   $VENV_DIR/bin/python"
echo "  Node.js:       $(command -v node 2>/dev/null || echo '要: ターミナル再起動後に確認')"
echo "  プロジェクト:  $TEAM_INFO_ROOT"
echo ""
echo "次のステップ:"
echo "  ・ターミナルを再起動して PATH を再読み込みしてください"
echo "  ・Claude Code: code $TEAM_INFO_ROOT"
echo ""
