#!/usr/bin/env bash
# =============================================================================
# team-info setup script for Windows Git Bash.
# Installs the same core tools as the Windows PowerShell setup while keeping
# Git Bash aliases, PATH entries, and TEAM_INFO_ROOT usable from Bash sessions.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; RESET='\033[0m'
info()    { echo -e "${BLUE}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
step()    { echo -e "\n${BOLD}=== $* ===${RESET}"; }

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) ;;
  *) error "このスクリプトは Windows Git Bash で実行してください。" ;;
esac

command -v cygpath >/dev/null 2>&1 || error "cygpath が見つかりません。Git Bash から実行してください。"
command -v powershell.exe >/dev/null 2>&1 || error "powershell.exe が見つかりません。Windows 上の Git Bash から実行してください。"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

is_repo_root_dir() {
  local candidate="$1"
  [[ -f "$candidate/AGENTS.md" && -f "$candidate/setup/setup_git_bash.sh" ]]
}

CURRENT_DIR="$(pwd -P)"
if is_repo_root_dir "$CURRENT_DIR"; then
  TEAM_INFO_ROOT_POSIX="$CURRENT_DIR"
else
  TEAM_INFO_ROOT_POSIX="$SCRIPT_REPO_ROOT"
fi
TEAM_INFO_ROOT_WIN="$(cygpath -w "$TEAM_INFO_ROOT_POSIX")"

NODE_VERSION="22.17.1"
PYTHON_VERSION="3.11.9"
CODEX_NPM_PACKAGE="@openai/codex"
CODEX_WINDOWS_INSTALLER_URL="https://chatgpt.com/codex/install.ps1"
FREEBUFF_NPM_PACKAGE="freebuff"

TEAM_INFO_ENV_DIR="$HOME/.config/team-info"
TEAM_INFO_ENV_FILE="$TEAM_INFO_ENV_DIR/env.sh"

ps_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

ps_command() {
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$1"
}

get_windows_env() {
  local name="$1"
  ps_command "[Environment]::GetEnvironmentVariable('$(ps_escape "$name")','Process')" | tr -d '\r'
}

USERPROFILE_WIN="$(cygpath -w "${USERPROFILE:-$(get_windows_env USERPROFILE)}")"
APPDATA_WIN="$(cygpath -w "${APPDATA:-$(get_windows_env APPDATA)}")"
LOCALAPPDATA_WIN="$(cygpath -w "${LOCALAPPDATA:-$(get_windows_env LOCALAPPDATA)}")"
PROGRAMFILES_WIN="$(cygpath -w "${PROGRAMFILES:-$(get_windows_env 'ProgramFiles')}")"
USERPROFILE_POSIX="$(cygpath -u "$USERPROFILE_WIN")"
APPDATA_POSIX="$(cygpath -u "$APPDATA_WIN")"
LOCALAPPDATA_POSIX="$(cygpath -u "$LOCALAPPDATA_WIN")"
PROGRAMFILES_POSIX="$(cygpath -u "$PROGRAMFILES_WIN")"
NPM_USER_PREFIX_WIN="$USERPROFILE_WIN\\.local\\npm"
NPM_USER_PREFIX_POSIX="$USERPROFILE_POSIX/.local/npm"
PYENV_WIN="$USERPROFILE_WIN\\.pyenv\\pyenv-win"
PYENV_POSIX="$USERPROFILE_POSIX/.pyenv/pyenv-win"
PYTHON311_POSIX="$PYENV_POSIX/versions/$PYTHON_VERSION/python.exe"
PYTHON311_WIN="$PYENV_WIN\\versions\\$PYTHON_VERSION\\python.exe"

append_line_if_missing() {
  local file="$1"
  local line="$2"
  mkdir -p "$(dirname "$file")"
  touch "$file"
  if ! grep -Fqx "$line" "$file"; then
    printf '%s\n' "$line" >> "$file"
  fi
}

ensure_path_entry() {
  local entry="$1"
  [[ -n "$entry" ]] || return
  case ":$PATH:" in
    *":$entry:"*) ;;
    *) export PATH="$entry:$PATH" ;;
  esac
}

prepend_path_entry() {
  local entry="$1"
  [[ -n "$entry" ]] || return
  export PATH="$entry:$PATH"
}

add_windows_user_path_entry() {
  local entry="$1"
  local entry_escaped
  entry_escaped="$(ps_escape "$entry")"
  ps_command "\$entry='$entry_escaped'; \$current=[Environment]::GetEnvironmentVariable('Path','User'); \$parts=@(); if(\$current){ \$parts=\$current -split ';' | Where-Object { \$_ } }; if(\$parts -notcontains \$entry){ [Environment]::SetEnvironmentVariable('Path', ((@(\$parts)+\$entry) -join ';'), 'User') }" >/dev/null
}

set_windows_user_env() {
  local name="$1"
  local value="$2"
  ps_command "[Environment]::SetEnvironmentVariable('$(ps_escape "$name")','$(ps_escape "$value")','User')" >/dev/null
}

ask_yes_no() {
  local question="$1"
  local default_answer="${2:-no}"
  local suffix answer
  if [[ "$default_answer" == "yes" ]]; then
    suffix="[y/n、未入力なら y]"
  else
    suffix="[y/n、未入力なら n]"
  fi

  while true; do
    read -rp "  $question $suffix: " answer
    answer="$(printf '%s' "$answer" | tr '[:upper:]' '[:lower:]' | tr -d '[:space:]')"
    case "$answer" in
      "")
        [[ "$default_answer" == "yes" ]]
        return
        ;;
      y) return 0 ;;
      n) return 1 ;;
      *) warn "y または n で入力してください。" ;;
    esac
  done
}

refresh_known_windows_paths() {
  ensure_path_entry "$NPM_USER_PREFIX_POSIX"
  ensure_path_entry "$USERPROFILE_POSIX/AppData/Roaming/npm"
  ensure_path_entry "$PYENV_POSIX/bin"
  ensure_path_entry "$PYENV_POSIX/shims"
  ensure_path_entry "$APPDATA_POSIX/nvm"
  ensure_path_entry "$LOCALAPPDATA_POSIX/nvm"
  ensure_path_entry "$LOCALAPPDATA_POSIX/Programs/OpenAI/Codex/bin"
  ensure_path_entry "$PROGRAMFILES_POSIX/nodejs"
  ensure_path_entry "$PROGRAMFILES_POSIX/GitHub CLI"
  ensure_path_entry "$PROGRAMFILES_POSIX/Rclone"
  ensure_path_entry "$PROGRAMFILES_POSIX/PowerShell/7"
}

command_exists() {
  command -v "$1" >/dev/null 2>&1 || command -v "$1.exe" >/dev/null 2>&1 || command -v "$1.cmd" >/dev/null 2>&1
}

install_with_winget() {
  local package_id="$1"
  local label="$2"
  command -v winget.exe >/dev/null 2>&1 || error "winget.exe が見つかりません。Microsoft Store の App Installer を入れてから再実行してください。"
  info "$label をインストールします..."
  winget.exe install --id "$package_id" --silent --accept-package-agreements --accept-source-agreements
  refresh_known_windows_paths
  success "$label インストール完了"
}

run_pyenv() {
  if command -v pyenv >/dev/null 2>&1; then
    pyenv "$@"
  elif command -v pyenv.bat >/dev/null 2>&1; then
    pyenv.bat "$@"
  elif [[ -f "$PYENV_POSIX/bin/pyenv.bat" ]]; then
    "$PYENV_POSIX/bin/pyenv.bat" "$@"
  else
    error "pyenv-win が見つかりません。"
  fi
}

get_nvm_exe() {
  local candidates=(
    "$APPDATA_POSIX/nvm/nvm.exe"
    "$LOCALAPPDATA_POSIX/nvm/nvm.exe"
  )
  local found
  found="$(command -v nvm.exe 2>/dev/null || true)"
  [[ -n "$found" ]] && { printf '%s\n' "$found"; return; }
  for candidate in "${candidates[@]}"; do
    [[ -f "$candidate" ]] && { printf '%s\n' "$candidate"; return; }
  done
}

get_node_symlink_posix() {
  local env_value
  env_value="$(get_windows_env NVM_SYMLINK)"
  if [[ -n "$env_value" ]]; then
    cygpath -u "$env_value"
    return
  fi
  printf '%s\n' "$PROGRAMFILES_POSIX/nodejs"
}

path_to_posix_maybe() {
  local path_value="$1"
  if [[ "$path_value" =~ ^[A-Za-z]:\\ ]]; then
    cygpath -u "$path_value"
  else
    printf '%s\n' "$path_value"
  fi
}

get_npm_global_bin_dir() {
  local prefix
  prefix="$(npm prefix -g 2>/dev/null | tr -d '\r' || true)"
  [[ -n "$prefix" ]] || return 1
  path_to_posix_maybe "$prefix"
}

ensure_npm_global_install_target() {
  local global_root global_root_posix
  mkdir -p "$NPM_USER_PREFIX_POSIX"
  ensure_path_entry "$NPM_USER_PREFIX_POSIX"
  add_windows_user_path_entry "$NPM_USER_PREFIX_WIN"

  global_root="$(npm root -g 2>/dev/null | tr -d '\r' || true)"
  global_root_posix="$(path_to_posix_maybe "$global_root")"
  if [[ -z "$global_root" || ! -w "$global_root_posix" ]]; then
    export NPM_CONFIG_PREFIX="$NPM_USER_PREFIX_WIN"
    warn "npm の global install 先に書き込めません: ${global_root:-unknown}"
    info "ユーザー領域 $NPM_USER_PREFIX_WIN に npm CLI を入れます"
  fi
}

install_npm_cli() {
  local label="$1"
  local package_name="$2"
  local command_name="$3"
  local installed_path existing_path npm_bin_dir candidate

  if ! command_exists npm; then
    warn "npm が見つかりません。Git Bash を開き直してから手動で実行してください:"
    warn "  NPM_CONFIG_PREFIX=\"$NPM_USER_PREFIX_WIN\" npm install -g $package_name"
    return 1
  fi

  existing_path="$(command -v "$command_name" 2>/dev/null || command -v "$command_name.cmd" 2>/dev/null || true)"
  if [[ -n "$existing_path" ]]; then
    info "$label を更新します..."
  else
    info "$label をグローバルに入れます..."
  fi

  ensure_npm_global_install_target
  npm_bin_dir="$(get_npm_global_bin_dir || true)"
  if [[ -n "$npm_bin_dir" ]]; then
    prepend_path_entry "$npm_bin_dir"
    add_windows_user_path_entry "$(cygpath -w "$npm_bin_dir")"
  fi

  if npm install -g "$package_name"; then
    hash -r 2>/dev/null || true
    refresh_known_windows_paths
    [[ -n "$npm_bin_dir" ]] && prepend_path_entry "$npm_bin_dir"
    installed_path="$(command -v "$command_name" 2>/dev/null || command -v "$command_name.cmd" 2>/dev/null || true)"
    if [[ -z "$installed_path" && -n "$npm_bin_dir" ]]; then
      for candidate in "$npm_bin_dir/$command_name" "$npm_bin_dir/$command_name.cmd"; do
        if [[ -f "$candidate" || -x "$candidate" ]]; then
          installed_path="$candidate"
          break
        fi
      done
    fi
    if [[ -n "$installed_path" ]]; then
      success "$label インストール完了: $installed_path"
      return 0
    fi
    warn "$label は npm install 済みですが、現在の PATH から $command_name が見つかりません。"
    [[ -n "$npm_bin_dir" ]] && warn "npm global bin を PATH に追加してください: $(cygpath -w "$npm_bin_dir")"
    return 1
  else
    installed_path="$(command -v "$command_name" 2>/dev/null || command -v "$command_name.cmd" 2>/dev/null || true)"
    if [[ -n "$installed_path" ]]; then
      warn "$label の更新に失敗しましたが、既存コマンドは利用できます: $installed_path"
      return 0
    fi
    warn "$label のインストールに失敗しました。あとで次を実行してください:"
    warn "  NPM_CONFIG_PREFIX=\"$NPM_USER_PREFIX_WIN\" npm install -g $package_name"
    return 1
  fi
}

verify_codex_cli() {
  local installed_path version_output version_line

  installed_path="$(command -v codex 2>/dev/null || command -v codex.exe 2>/dev/null || command -v codex.cmd 2>/dev/null || true)"
  [[ -n "$installed_path" ]] || return 1

  if version_output="$(codex --version 2>&1 | tr -d '\r')"; then
    version_line="$(printf '%s\n' "$version_output" | tail -n 1)"
    success "Codex CLI 利用可能: $installed_path (${version_line:-version unknown})"
    return 0
  fi

  warn "codex --version の実行に失敗しました: $installed_path"
  return 1
}

install_codex_cli() {
  local codex_bin_win codex_bin_posix

  codex_bin_win="$LOCALAPPDATA_WIN\\Programs\\OpenAI\\Codex\\bin"
  codex_bin_posix="$LOCALAPPDATA_POSIX/Programs/OpenAI/Codex/bin"
  prepend_path_entry "$codex_bin_posix"
  add_windows_user_path_entry "$codex_bin_win"

  if command_exists codex; then
    info "Codex CLI を公式 standalone installer で更新します..."
  else
    info "Codex CLI を公式 standalone installer で入れます..."
  fi

  if ps_command "\$env:CODEX_NON_INTERACTIVE = '1'; irm '$CODEX_WINDOWS_INSTALLER_URL' | iex"; then
    refresh_known_windows_paths
    prepend_path_entry "$codex_bin_posix"
    if verify_codex_cli; then
      return 0
    fi
    warn "standalone installer は完了しましたが、codex が PATH から確認できません。"
  else
    warn "Codex CLI standalone installer に失敗しました。npm fallback を試します。"
  fi

  install_npm_cli "Codex CLI" "$CODEX_NPM_PACKAGE" "codex"
}

get_python_user_scripts_dir() {
  local user_base
  user_base="$("$PYTHON311_POSIX" -c 'import site; print(site.USER_BASE)' | tr -d '\r')"
  printf '%s/Scripts\n' "$(path_to_posix_maybe "$user_base")"
}

get_git_config_value() {
  local scope="$1"
  local key="$2"
  if [[ "$scope" == "global" ]]; then
    git config --global --get "$key" 2>/dev/null || true
  else
    git -C "$TEAM_INFO_ROOT_POSIX" config --get "$key" 2>/dev/null || true
  fi
}

read_git_config_input() {
  local label="$1"
  local current_value="${2:-}"
  local input_value
  if [[ -n "$current_value" ]]; then
    read -rp "  $label [$current_value]: " input_value
    if [[ -z "${input_value// }" ]]; then
      printf '%s\n' "$current_value"
      return
    fi
    printf '%s\n' "$input_value"
    return
  fi
  while true; do
    read -rp "  $label: " input_value
    if [[ -n "${input_value// }" ]]; then
      printf '%s\n' "$input_value"
      return
    fi
    warn "$label は必須です。"
  done
}

set_git_config_value() {
  local scope="$1"
  local key="$2"
  local value="$3"
  if [[ "$scope" == "global" ]]; then
    git config --global "$key" "$value"
  else
    git -C "$TEAM_INFO_ROOT_POSIX" config "$key" "$value"
  fi
}

configure_git_identity() {
  local local_name local_email global_name global_email
  local default_name default_email git_name git_email
  step "2b. Git user identity"
  local_name="$(get_git_config_value local user.name)"
  local_email="$(get_git_config_value local user.email)"
  global_name="$(get_git_config_value global user.name)"
  global_email="$(get_git_config_value global user.email)"

  if [[ -n "$local_name" && -n "$local_email" ]]; then
    success "このリポジトリの Git user 設定済み: $local_name <$local_email>"
    return
  fi

  if [[ -n "$global_name" && -n "$global_email" ]]; then
    success "Git global user 設定済み: $global_name <$global_email>"
    if ask_yes_no "この global identity をこのリポジトリにも設定しますか？" yes; then
      set_git_config_value local user.name "$global_name"
      set_git_config_value local user.email "$global_email"
      success "このリポジトリの Git user を設定しました: $global_name <$global_email>"
      return
    fi
  fi

  info "コミットに使う Git identity を入力してください。"
  default_name="${local_name:-$global_name}"
  default_email="${local_email:-$global_email}"
  git_name="$(read_git_config_input user.name "$default_name")"
  git_email="$(read_git_config_input user.email "$default_email")"

  if ask_yes_no "今後のリポジトリ用に global にも保存しますか？" yes; then
    set_git_config_value global user.name "$git_name"
    set_git_config_value global user.email "$git_email"
    success "Git global user を設定しました: $git_name <$git_email>"
  fi

  set_git_config_value local user.name "$git_name"
  set_git_config_value local user.email "$git_email"
  success "このリポジトリの Git user を設定しました: $git_name <$git_email>"
}

gh_auth_status_ok() {
  gh auth status --hostname github.com >/dev/null 2>&1
}

ensure_github_auth() {
  local attempt=1
  local max_attempts=3

  while (( attempt <= max_attempts )); do
    if gh_auth_status_ok; then
      success "GitHub CLI (gh) 認証済み"
      break
    fi

    info "GitHub CLI (gh) の認証を開始します（試行 $attempt/$max_attempts）。ブラウザでログインしてください..."
    gh auth login --hostname github.com --git-protocol https --web || true

    if gh_auth_status_ok; then
      success "GitHub CLI (gh) 認証完了"
      break
    fi

    if (( attempt == max_attempts )); then
      error "GitHub CLI (gh) の認証確認に失敗しました。'gh auth status --hostname github.com' を確認してください。"
    fi
    warn "GitHub CLI (gh) の認証を確認できませんでした。もう一度ログインを試します。"
    attempt=$((attempt + 1))
  done

  if gh auth setup-git --hostname github.com >/dev/null 2>&1; then
    success "GitHub CLI を Git の credential helper に設定しました"
  else
    warn "GitHub CLI の Git credential helper 設定に失敗しました。必要なら手動で 'gh auth setup-git --hostname github.com' を実行してください。"
  fi
}

github_repo_access_ok() {
  git -C "$TEAM_INFO_ROOT_POSIX" ls-remote --exit-code origin HEAD >/dev/null 2>&1
}

ensure_github_repo_access() {
  local attempt=1
  local max_attempts=3

  while (( attempt <= max_attempts )); do
    if github_repo_access_ok; then
      success "GitHub リポジトリアクセス確認完了"
      return
    fi

    warn "https://github.com/Shoma-DS/team-info.git にアクセスできません。GitHub の招待を承認していない、または認証が古い可能性があります。"
    if (( attempt == max_attempts )); then
      error "https://github.com/Shoma-DS/team-info.git にアクセスできません。GitHub の招待を承認してから setup を再実行してください。不明な場合は sho に確認してください。"
    fi

    if ask_yes_no "GitHub の招待承認状況を確認し、gh auth login をやり直して再試行しますか？" yes; then
      gh auth login --hostname github.com --git-protocol https --web || true
      gh auth setup-git --hostname github.com >/dev/null 2>&1 || true
    else
      error "https://github.com/Shoma-DS/team-info.git にアクセスできません。GitHub の招待を承認してから setup を再実行してください。不明な場合は sho に確認してください。"
    fi
    attempt=$((attempt + 1))
  done
}

write_git_bash_env_file() {
  mkdir -p "$TEAM_INFO_ENV_DIR"
  cat > "$TEAM_INFO_ENV_FILE" <<EOF
export TEAM_INFO_ROOT="$TEAM_INFO_ROOT_POSIX"

case ":\$PATH:" in
  *":$NPM_USER_PREFIX_POSIX:"*) ;;
  *) export PATH="$NPM_USER_PREFIX_POSIX:\$PATH" ;;
esac

case ":\$PATH:" in
  *":$LOCALAPPDATA_POSIX/Programs/OpenAI/Codex/bin:"*) ;;
  *) export PATH="$LOCALAPPDATA_POSIX/Programs/OpenAI/Codex/bin:\$PATH" ;;
esac

case ":\$PATH:" in
  *":$USERPROFILE_POSIX/AppData/Roaming/npm:"*) ;;
  *) export PATH="$USERPROFILE_POSIX/AppData/Roaming/npm:\$PATH" ;;
esac

# チームツール起動エイリアス
alias setup='bash "\$TEAM_INFO_ROOT/setup/setup_git_bash.sh"'
alias x-post='bash "\$TEAM_INFO_ROOT/.agent/skills/x-post-writer/scripts/start_preview.sh"'
alias remotion='npm --prefix "\$TEAM_INFO_ROOT/Remotion/my-video" run dev'
alias remodex='npx remodex'
alias renda='bash "\$TEAM_INFO_ROOT/Remotion/scripts/render_to_outputs.sh"'
EOF

  append_line_if_missing "$HOME/.bashrc" "[ -f \"$TEAM_INFO_ENV_FILE\" ] && source \"$TEAM_INFO_ENV_FILE\""
  append_line_if_missing "$HOME/.bash_profile" "[ -f \"$TEAM_INFO_ENV_FILE\" ] && source \"$TEAM_INFO_ENV_FILE\""
}

echo -e "${BOLD}"
echo "======================================================"
echo "       team-info setup (Windows Git Bash)"
echo "======================================================"
echo -e "${RESET}"
info "Project root (Git Bash): $TEAM_INFO_ROOT_POSIX"
info "Project root (Windows):  $TEAM_INFO_ROOT_WIN"
refresh_known_windows_paths

step "1. winget / PowerShell / UTF-8"
command -v winget.exe >/dev/null 2>&1 || error "winget.exe が見つかりません。Microsoft Store の App Installer を入れてから再実行してください。"
success "winget: $(winget.exe --version | tr -d '\r')"
set_windows_user_env "PYTHONUTF8" "1"
set_windows_user_env "PYTHONIOENCODING" "utf-8"
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
if command_exists pwsh; then
  success "PowerShell 7 インストール済み: $(pwsh --version 2>/dev/null | tr -d '\r' | head -1)"
else
  install_with_winget "Microsoft.PowerShell" "PowerShell 7"
fi
success "UTF-8 env set: PYTHONUTF8=1, PYTHONIOENCODING=utf-8"

step "2. Git / rclone"
if command_exists git; then
  success "Git インストール済み: $(git --version)"
else
  install_with_winget "Git.Git" "Git"
fi
configure_git_identity

if command_exists rclone; then
  success "rclone インストール済み: $(rclone version | head -1)"
else
  install_with_winget "Rclone.Rclone" "rclone"
fi

if git lfs version >/dev/null 2>&1; then
  git lfs install --skip-repo >/dev/null 2>&1 || warn "git lfs install --skip-repo に失敗しました。"
  success "git lfs を確認しました"
else
  warn "git lfs が見つかりません。Git を開き直すか、Git for Windows を再インストールしてください。"
fi

step "3. GitHub access and repo connection"
if command_exists gh; then
  success "GitHub CLI (gh) インストール済み: $(gh --version | head -1)"
else
  install_with_winget "GitHub.cli" "GitHub CLI (gh)"
fi

ensure_github_auth

git -C "$TEAM_INFO_ROOT_POSIX" remote set-url origin https://github.com/Shoma-DS/team-info.git
success "Remote URL set: https://github.com/Shoma-DS/team-info.git"
ensure_github_repo_access

step "4. pyenv-win + Python $PYTHON_VERSION"
if [[ ! -d "$PYENV_POSIX" ]]; then
  info "pyenv-win をインストールします..."
  ps_command "\$out=Join-Path \$env:TEMP 'team-info-pyenv-win-install.ps1'; Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1' -OutFile \$out; & \$out"
  success "pyenv-win インストール完了"
else
  success "pyenv-win インストール済み"
fi
set_windows_user_env "PYENV" "$PYENV_WIN"
add_windows_user_path_entry "$PYENV_WIN\\bin"
add_windows_user_path_entry "$PYENV_WIN\\shims"
refresh_known_windows_paths

if run_pyenv versions 2>&1 | tr -d '\r' | grep -q "$PYTHON_VERSION"; then
  success "Python $PYTHON_VERSION インストール済み"
else
  info "Python $PYTHON_VERSION をインストールします..."
  run_pyenv install "$PYTHON_VERSION"
  success "Python $PYTHON_VERSION インストール完了"
fi
[[ -x "$PYTHON311_POSIX" ]] || error "Python $PYTHON_VERSION が見つかりません: $PYTHON311_POSIX"
info "Python: $PYTHON311_WIN ($("$PYTHON311_POSIX" --version | tr -d '\r'))"

step "5. Python runtime policy"
success "Python 3.11 を使う土台を作りました"
warn "Remotion / Docker runtime や Python パッケージ群は、必要なスキルの初回実行時に準備します。"

step "6. uv"
PYTHON_USER_SCRIPTS_POSIX="$(get_python_user_scripts_dir)"
PYTHON_USER_SCRIPTS_WIN="$(cygpath -w "$PYTHON_USER_SCRIPTS_POSIX")"
ensure_path_entry "$PYTHON_USER_SCRIPTS_POSIX"
add_windows_user_path_entry "$PYTHON_USER_SCRIPTS_WIN"
if command_exists uv; then
  success "uv インストール済み"
else
  info "uv を入れます..."
  "$PYTHON311_POSIX" -m pip install --user uv
  success "uv インストール完了"
fi

step "7. TEAM_INFO_ROOT / Git Bash aliases"
export TEAM_INFO_ROOT="$TEAM_INFO_ROOT_POSIX"
set_windows_user_env "TEAM_INFO_ROOT" "$TEAM_INFO_ROOT_WIN"
write_git_bash_env_file
RUNTIME_SCRIPT_WIN="$(cygpath -w "$TEAM_INFO_ROOT_POSIX/.agent/skills/common/scripts/team_info_runtime.py")"
if "$PYTHON311_POSIX" "$RUNTIME_SCRIPT_WIN" setup-local-machine --repo-root "$TEAM_INFO_ROOT_WIN" --shell sh >/dev/null; then
  success "TEAM_INFO_ROOT を保存しました"
else
  warn "TEAM_INFO_ROOT の runtime 保存に失敗しました。"
fi
REGISTER_ALIASES_WIN="$(cygpath -w "$TEAM_INFO_ROOT_POSIX/.agent/skills/common/scripts/register_aliases.py")"
if "$PYTHON311_POSIX" "$REGISTER_ALIASES_WIN" --root "$TEAM_INFO_ROOT_WIN" >/dev/null 2>&1; then
  success "PowerShell 用 alias 登録も確認しました"
else
  warn "PowerShell 用 alias 登録はスキップされました"
fi

step "8. nvm-windows + Node.js $NODE_VERSION"
NVM_EXE="$(get_nvm_exe || true)"
if [[ -z "$NVM_EXE" ]]; then
  install_with_winget "CoreyButler.NVMforWindows" "nvm-windows"
  NVM_EXE="$(get_nvm_exe || true)"
fi

if [[ -n "$NVM_EXE" ]]; then
  NVM_HOME_POSIX="$(dirname "$NVM_EXE")"
  NVM_HOME_WIN="$(cygpath -w "$NVM_HOME_POSIX")"
  NODE_SYMLINK_POSIX="$(get_node_symlink_posix)"
  NODE_SYMLINK_WIN="$(cygpath -w "$NODE_SYMLINK_POSIX")"
  set_windows_user_env "NVM_HOME" "$NVM_HOME_WIN"
  set_windows_user_env "NVM_SYMLINK" "$NODE_SYMLINK_WIN"
  add_windows_user_path_entry "$NVM_HOME_WIN"
  add_windows_user_path_entry "$NODE_SYMLINK_WIN"
  ensure_path_entry "$NVM_HOME_POSIX"
  ensure_path_entry "$NODE_SYMLINK_POSIX"

  if "$NVM_EXE" list 2>&1 | tr -d '\r' | grep -q "$NODE_VERSION"; then
    success "Node.js $NODE_VERSION インストール済み"
  else
    info "Node.js $NODE_VERSION をインストールします..."
    "$NVM_EXE" install "$NODE_VERSION"
    success "Node.js $NODE_VERSION インストール完了"
  fi
  "$NVM_EXE" use "$NODE_VERSION" >/dev/null
  refresh_known_windows_paths
else
  warn "nvm.exe が見つかりません。Git Bash を開き直して setup を再実行してください。"
fi

if command_exists node && command_exists npm; then
  info "Node.js: $(node --version | tr -d '\r'), npm: $(npm --version | tr -d '\r')"
else
  warn "node / npm が見つかりません。Git Bash を開き直して setup を再実行してください。"
fi

step "9. Codex CLI"
if ! install_codex_cli; then
  warn "Codex CLI が使える状態になっていません。上の npm / PATH メッセージを確認してください。"
fi

step "9b. Codex custom prompts"
CODEX_PROMPTS_SCRIPT_WIN="$(cygpath -w "$TEAM_INFO_ROOT_POSIX/scripts/sync_cross_cli_commands.py")"
if [[ -f "$TEAM_INFO_ROOT_POSIX/scripts/sync_cross_cli_commands.py" ]]; then
  if "$PYTHON311_POSIX" "$CODEX_PROMPTS_SCRIPT_WIN" --repo-only; then
    success "Codex prompt sources をこのリポジトリの .codex/prompts に同期しました。"
  else
    warn "Codex prompt sources の同期に失敗しました。"
  fi
else
  warn "Codex prompt 同期スクリプトが見つかりません。"
fi

step "10. Freebuff CLI"
if ! install_npm_cli "Freebuff CLI" "$FREEBUFF_NPM_PACKAGE" "freebuff"; then
  warn "Freebuff CLI が使える状態になっていません。必要ならあとで手動インストールしてください。"
fi

step "10a. Headroom"
HEADROOM_INSTALLER_WIN="$(cygpath -w "$TEAM_INFO_ROOT_POSIX/setup/headroom/install.ps1")"
if [[ -f "$TEAM_INFO_ROOT_POSIX/setup/headroom/install.ps1" ]]; then
  if powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$HEADROOM_INSTALLER_WIN" -PythonExe "$PYTHON311_WIN" -RepoRoot "$TEAM_INFO_ROOT_WIN"; then
    success "Headroom を導入しました"
  else
    warn "Headroom の導入に失敗しました（setup は続行）"
  fi
else
  warn "Headroom installer not found: $HEADROOM_INSTALLER_WIN"
fi

step "11. Git hooks"
if git -C "$TEAM_INFO_ROOT_POSIX" config core.hooksPath .githooks; then
  success "core.hooksPath を .githooks に設定しました"
else
  warn "core.hooksPath の設定に失敗しました。"
fi

step "12. Lazy setup notice"
warn "以下は setup では入れません。必要なスキルを初めて使うタイミングで準備します。"
warn "  - Remotion / VOICEVOX / Docker runtime"
warn "  - Canva 補助などの追加開発依存"
warn "  - Agent Reach / OpenClaw / Obsidian / Claudian"
warn "  - shared-agent-assets の同期処理"
warn "  - clone-website 用の Node 24 workspace 依存"

step "13. Docker optional"
if command_exists docker; then
  success "Docker インストール済み: $(docker --version | tr -d '\r')"
  warn "Docker image build / pull は重いため、必要なスキルの初回実行時に行います。"
else
  warn "Docker が見つかりません。必要時に WSL2 Docker Engine + Compose v2 を準備してください。"
  warn "PowerShell で実行: & \"\$env:TEAM_INFO_ROOT\\setup\\setup_wsl_docker_engine.ps1\" -Distro Ubuntu"
fi

VERIFY_STATUS=0
step "14. Verify setup"
VERIFY_SCRIPT_WIN="$(cygpath -w "$TEAM_INFO_ROOT_POSIX/setup/verify_setup.py")"
if "$PYTHON311_POSIX" "$VERIFY_SCRIPT_WIN" --repo-root "$TEAM_INFO_ROOT_WIN"; then
  success "セットアップ検証完了"
else
  VERIFY_STATUS=$?
  warn "セットアップ検証で不足が見つかりました。ログを確認してください。"
fi

echo ""
if [[ "$VERIFY_STATUS" -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}"
  echo "*******************************************************"
  echo ""
  echo "  ####   ###   #   #  ####   #      #####  #####  #####"
  echo " #      #   #  ## ##  #   #  #      #        #    #    "
  echo " #      #   #  # # #  ####   #      ####     #    #### "
  echo " #      #   #  #   #  #      #      #        #    #    "
  echo "  ####   ###   #   #  #      #####  #####    #    #####"
  echo ""
  echo "        Setup completed! Great job!"
  echo ""
  echo "*******************************************************"
  echo -e "${RESET}"
else
  echo -e "${YELLOW}${BOLD}Setup finished with warnings${RESET}"
fi
echo "Key paths:"
echo "  Python:        $PYTHON311_WIN"
echo "  Node.js:       $(command -v node 2>/dev/null || command -v node.exe 2>/dev/null || echo '要: Git Bash 再起動後に確認')"
echo "  Codex CLI:     $(command -v codex 2>/dev/null || command -v codex.cmd 2>/dev/null || echo '要: setup 再実行か手動インストール')"
echo "  Freebuff CLI:  $(command -v freebuff 2>/dev/null || command -v freebuff.cmd 2>/dev/null || echo '要: setup 再実行か手動インストール')"
echo "  Project bash:  $TEAM_INFO_ROOT_POSIX"
echo "  Project win:   $TEAM_INFO_ROOT_WIN"
echo "  Bash env:      $TEAM_INFO_ENV_FILE"
echo "  Verify result: $([[ "$VERIFY_STATUS" -eq 0 ]] && echo 'passed' || echo 'needs review')"
echo ""
echo "Next steps:"
echo "  - Git Bash を開き直して PATH と alias を読み直してください"
echo "  - setup / x-post / remotion / remodex / renda は Git Bash でも使えます"
echo "  - Windows の日本語/UTF-8 作業では pwsh も利用できます"
echo ""

if command_exists codex; then
  if ask_yes_no "Codex を今すぐ起動しますか？" no; then
    exec codex
  fi
fi

exit "$VERIFY_STATUS"
