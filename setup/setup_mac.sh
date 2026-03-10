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
PYTHON_VERSION="3.11.9"
SHELL_RC="$HOME/.zshrc"
SECRETS_DIR="$HOME/.secrets"
CANVA_CREDENTIALS_FILE="$SECRETS_DIR/canva_credentials.txt"
CANVA_AUTH_DIR="$TEAM_INFO_ROOT/Remotion/scripts/canva_auth"
DIFY_ROOT="$TEAM_INFO_ROOT/docker/dify"
DIFY_API_DIR="$DIFY_ROOT/api"
DIFY_WEB_DIR="$DIFY_ROOT/web"
DIFY_WEB_NVMRC="$DIFY_WEB_DIR/.nvmrc"
DIFY_WEB_PACKAGE_JSON="$DIFY_WEB_DIR/package.json"
DIFY_SDK_DIR="$DIFY_ROOT/sdks/nodejs-client"
if [[ "${SHELL:-}" == *"bash"* ]]; then
  SHELL_RC="$HOME/.bash_profile"
fi

append_line_if_missing() {
  local file="$1"
  local line="$2"

  touch "$file"
  if ! grep -Fqx "$line" "$file"; then
    printf '%s\n' "$line" >> "$file"
  fi
}

copy_if_missing() {
  local source="$1"
  local target="$2"

  if [[ -f "$source" && ! -f "$target" ]]; then
    cp "$source" "$target"
  fi
}

get_pnpm_version() {
  local package_json="$1"
  "$PYTHON311" -c 'import json, sys
package_manager = json.load(open(sys.argv[1], encoding="utf-8")).get("packageManager", "")
if package_manager.startswith("pnpm@"):
    print(package_manager.split("@", 1)[1].split("+", 1)[0])
' "$package_json"
}

get_python_user_bin() {
  local user_base
  user_base="$("$PYTHON311" -c 'import site; print(site.USER_BASE)')"
  printf '%s/bin\n' "$user_base"
}

ensure_canva_credentials_template() {
  mkdir -p "$SECRETS_DIR"
  if [[ ! -f "$CANVA_CREDENTIALS_FILE" ]]; then
    cat > "$CANVA_CREDENTIALS_FILE" <<'EOF'
# Canva API credentials
CANVA_CLIENT_ID=
CANVA_CLIENT_SECRET=
EOF
    chmod 600 "$CANVA_CREDENTIALS_FILE" || true
    warn "Canva の鍵ファイルを作りました: $CANVA_CREDENTIALS_FILE"
  else
    success "Canva の鍵ファイルあり: $CANVA_CREDENTIALS_FILE"
  fi
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
step "3. 基本ツール (git, wget, tesseract, tesseract-lang, ffmpeg)"
BREW_PACKAGES=(git wget tesseract tesseract-lang ffmpeg)
for pkg in "${BREW_PACKAGES[@]}"; do
  if brew list "$pkg" &>/dev/null; then
    success "$pkg インストール済み"
  else
    info "$pkg をインストールします..."
    brew install "$pkg"
    success "$pkg インストール完了"
  fi
done

# ── 4. pyenv + Python ─────────────────────────────────────────────────────────
step "4. pyenv + Python $PYTHON_VERSION"
if ! command -v pyenv &>/dev/null; then
  info "pyenv をインストールします..."
  brew install pyenv
  # shell 設定に追加
  append_line_if_missing "$SHELL_RC" '# pyenv'
  append_line_if_missing "$SHELL_RC" 'export PYENV_ROOT="$HOME/.pyenv"'
  append_line_if_missing "$SHELL_RC" 'export PATH="$PYENV_ROOT/bin:$PATH"'
  append_line_if_missing "$SHELL_RC" 'eval "$(pyenv init -)"'
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

# ── 7. uv ─────────────────────────────────────────────────────────────────────
step "7. uv"
PYTHON_USER_BIN="$(get_python_user_bin)"
append_line_if_missing "$SHELL_RC" "export PATH=\"$PYTHON_USER_BIN:\$PATH\""
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

# ── 9. TEAM_INFO_ROOT ──────────────────────────────────────────────────────────
step "9. TEAM_INFO_ROOT"
export TEAM_INFO_ROOT
append_line_if_missing "$SHELL_RC" "export TEAM_INFO_ROOT=\"$TEAM_INFO_ROOT\""
if "$PYTHON311" "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" \
  setup-local-machine --repo-root "$TEAM_INFO_ROOT" --shell sh >/dev/null; then
  success "TEAM_INFO_ROOT を保存しました: $TEAM_INFO_ROOT"
else
  warn "TEAM_INFO_ROOT の保存に失敗しました。必要なら手動で設定してください。"
fi

# ── 10. npm パッケージ (Remotion) ─────────────────────────────────────────────
step "10. npm パッケージ (Remotion/my-video)"
REMOTION_DIR="$TEAM_INFO_ROOT/Remotion/my-video"
if [[ -d "$REMOTION_DIR" ]]; then
  info "npm install を実行します..."
  cd "$REMOTION_DIR"
  npm install
  success "npm install 完了"
else
  warn "Remotion/my-video が見つかりません: $REMOTION_DIR"
fi

# ── 11. MCP サーバー (VOICEVOX) ───────────────────────────────────────────────
step "11. npm パッケージ (mcp-servers/voicevox)"
VOICEVOX_MCP_DIR="$TEAM_INFO_ROOT/mcp-servers/voicevox"
if [[ -d "$VOICEVOX_MCP_DIR" ]]; then
  cd "$VOICEVOX_MCP_DIR"
  npm install
  if npm run build; then
    success "voicevox MCP build 完了"
  else
    warn "voicevox MCP build に失敗しました。あとで確認してください。"
  fi
  success "voicevox MCP npm install 完了"
fi

# ── 12. npm パッケージ (Canva 補助) ──────────────────────────────────────────
step "12. npm パッケージ (Remotion/scripts/canva_auth)"
if [[ -d "$CANVA_AUTH_DIR" ]]; then
  cd "$CANVA_AUTH_DIR"
  npm install
  success "Canva 補助 npm install 完了"
fi

# ── 13. Dify 開発環境 ─────────────────────────────────────────────────────────
step "13. Dify 開発環境"
if [[ -d "$DIFY_ROOT" ]]; then
  copy_if_missing "$DIFY_API_DIR/.env.example" "$DIFY_API_DIR/.env"
  copy_if_missing "$DIFY_WEB_DIR/.env.example" "$DIFY_WEB_DIR/.env.local"
  copy_if_missing "$DIFY_ROOT/docker/middleware.env.example" "$DIFY_ROOT/docker/middleware.env"

  if [[ -f "$DIFY_API_DIR/pyproject.toml" ]]; then
    info "Dify API の依存を入れます..."
    if (cd "$DIFY_API_DIR" && uv sync --group dev); then
      success "Dify API の依存を入れました"
    else
      warn "Dify API の依存で止まりました。あとで uv sync --group dev を見てください。"
    fi
  fi

  if [[ -f "$DIFY_WEB_NVMRC" ]]; then
    DIFY_NODE_VERSION="$(tr -d '[:space:]' < "$DIFY_WEB_NVMRC")"
    if [[ -n "$DIFY_NODE_VERSION" ]]; then
      info "Dify 用の Node.js $DIFY_NODE_VERSION を入れます..."
      nvm install "$DIFY_NODE_VERSION"
      nvm use "$DIFY_NODE_VERSION"

      if [[ -f "$DIFY_WEB_PACKAGE_JSON" ]]; then
        DIFY_PNPM_VERSION="$(get_pnpm_version "$DIFY_WEB_PACKAGE_JSON")"
        if command -v corepack &>/dev/null; then
          corepack enable
          if [[ -n "$DIFY_PNPM_VERSION" ]]; then
            corepack prepare "pnpm@$DIFY_PNPM_VERSION" --activate
          fi

          if (cd "$DIFY_WEB_DIR" && pnpm install); then
            success "Dify Web の依存を入れました"
          else
            warn "Dify Web の依存で止まりました。あとで pnpm install を見てください。"
          fi

          if [[ -f "$DIFY_SDK_DIR/package.json" ]]; then
            if (cd "$DIFY_SDK_DIR" && pnpm install); then
              success "Dify SDK の依存を入れました"
            else
              warn "Dify SDK の依存で止まりました。あとで pnpm install を見てください。"
            fi
          fi
        else
          warn "corepack が見つからないため、Dify の pnpm 準備を飛ばしました。"
        fi
      fi

      nvm use "$NODE_VERSION"
    fi
  fi
else
  warn "docker/dify が見つからないため、Dify の準備は飛ばしました。"
fi

# ── 14. 秘密ファイルの下準備 ───────────────────────────────────────────────
step "14. 秘密ファイルの下準備"
ensure_canva_credentials_template
warn "Canva を使うときは $CANVA_CREDENTIALS_FILE に鍵を書いてください。"
warn "VOICEVOX 本体アプリは別で入れて起動してください。"

# ── 15. Docker 確認 ───────────────────────────────────────────────────────────
step "15. Docker"
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
echo "  SHELL_RC:      $SHELL_RC"
echo "  Canva secrets: $CANVA_CREDENTIALS_FILE"
echo ""
echo "次のステップ:"
echo "  ・ターミナルを再起動して PATH を再読み込みしてください"
echo "  ・Claude Code: code $TEAM_INFO_ROOT"
echo ""
