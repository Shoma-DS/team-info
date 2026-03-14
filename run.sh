#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WAIT_SECONDS="${DOCKER_ENGINE_WAIT_SECONDS:-180}"
SLEEP_SECONDS="${DOCKER_ENGINE_POLL_SECONDS:-2}"
PROJECT_NAME="auto"
ACTION="up"
COMPOSE_ARGS=()

log() {
  printf '[INFO] %s\n' "$*"
}

warn() {
  printf '[WARN] %s\n' "$*" >&2
}

error() {
  printf '[ERROR] %s\n' "$*" >&2
  exit 1
}

notify() {
  printf '\a'
}

usage() {
  cat <<'EOF'
Usage:
  ./run.sh [--project auto|current|n8n|dify] [--action up|down|stop|start|restart|ps] [docker compose args...]

Examples:
  ./run.sh
  ./run.sh --project dify -d
  ./run.sh --project n8n
  ./run.sh --project dify --action down
EOF
}

docker_cli_ready() {
  docker --version >/dev/null 2>&1
}

docker_engine_ready() {
  docker info >/dev/null 2>&1 || docker ps >/dev/null 2>&1
}

docker_compose_ready() {
  docker compose version >/dev/null 2>&1
}

wait_for_enter_install() {
  notify
  cat <<'EOF'
Docker Desktop がインストールされていません。

以下のページから Docker Desktop をダウンロードしてインストールしてください。

https://www.docker.com/ja-jp/get-started/

インストールが完了したら Enter を押して続行してください。
EOF
  read -r
}

ensure_docker_cli() {
  until docker_cli_ready; do
    wait_for_enter_install
  done
  log "Docker CLI を確認しました: $(docker --version)"
}

start_docker_desktop() {
  case "$(uname -s)" in
    Darwin)
      log "Docker Desktop を起動します。"
      open -a Docker >/dev/null 2>&1 || error "Docker Desktop の起動に失敗しました。"
      ;;
    Linux)
      if docker desktop start >/dev/null 2>&1; then
        log "Docker Desktop を起動しました。"
      elif command -v systemctl >/dev/null 2>&1; then
        warn "docker desktop start は使えませんでした。Docker デーモンの起動を試みます。"
        if systemctl --user start docker-desktop >/dev/null 2>&1; then
          log "docker-desktop を起動しました。"
        elif sudo systemctl start docker >/dev/null 2>&1; then
          log "docker サービスを起動しました。"
        else
          warn "Docker の自動起動に失敗しました。Docker Desktop または Docker Engine を手動で起動してください。"
        fi
      else
        warn "Docker の自動起動方法を見つけられませんでした。Docker Desktop または Docker Engine を手動で起動してください。"
      fi
      ;;
    *)
      warn "この OS の自動起動は未対応です。Docker Desktop を手動で起動してください。"
      ;;
  esac
}

wait_for_docker_engine() {
  local elapsed=0
  while ! docker_engine_ready; do
    if (( elapsed == 0 )); then
      start_docker_desktop
    fi
    if (( elapsed >= WAIT_SECONDS )); then
      error "Docker Engine の起動待機がタイムアウトしました。Docker Desktop の状態を確認してください。"
    fi
    log "Waiting for Docker Engine to start..."
    sleep "$SLEEP_SECONDS"
    elapsed=$((elapsed + SLEEP_SECONDS))
  done
  log "Docker Engine が利用可能になりました。"
}

compose_file_in_dir() {
  local dir="$1"
  local name
  for name in docker-compose.yml docker-compose.yaml compose.yml compose.yaml; do
    if [[ -f "$dir/$name" ]]; then
      printf '%s\n' "$dir/$name"
      return 0
    fi
  done
  return 1
}

project_dir_from_name() {
  case "$1" in
    auto|"")
      return 1
      ;;
    current)
      printf '%s\n' "$PWD"
      return 0
      ;;
    n8n)
      printf '%s\n' "$SCRIPT_DIR/docker/n8n"
      return 0
      ;;
    dify)
      printf '%s\n' "$SCRIPT_DIR/docker/dify/docker"
      return 0
      ;;
    *)
      error "不明な project です: $1"
      ;;
  esac
}

select_compose_project() {
  local requested_project="${1:-auto}"
  local current_file
  local -a candidates=()
  local -a labels=()
  local repo_candidate

  if [[ "$requested_project" != "auto" ]]; then
    local explicit_dir
    explicit_dir="$(project_dir_from_name "$requested_project")"
    if compose_file_in_dir "$explicit_dir" >/dev/null; then
      printf '%s\n' "$explicit_dir"
      return 0
    fi
    error "compose ファイルが見つかりません: $explicit_dir"
  fi

  if current_file="$(compose_file_in_dir "$PWD")"; then
    printf '%s\n' "$PWD"
    return 0
  fi

  for repo_candidate in \
    "$SCRIPT_DIR/docker/n8n" \
    "$SCRIPT_DIR/docker/dify/docker"
  do
    if compose_file_in_dir "$repo_candidate" >/dev/null; then
      candidates+=("$repo_candidate")
      labels+=("${repo_candidate#$SCRIPT_DIR/}")
    fi
  done

  if (( ${#candidates[@]} == 0 )); then
    error "docker compose の対象が見つかりません。compose ファイルがあるディレクトリで実行するか、既知の compose プロジェクトを用意してください。"
  fi

  if (( ${#candidates[@]} == 1 )); then
    printf '%s\n' "${candidates[0]}"
    return 0
  fi

  notify
  printf 'docker compose %s の対象を選んでください。\n' "$ACTION"
  local i=1
  local selection
  for selection in "${labels[@]}"; do
    printf '  %d. %s\n' "$i" "$selection"
    i=$((i + 1))
  done

  while true; do
    read -r -p "番号を入力してください: " selection
    if [[ "$selection" =~ ^[0-9]+$ ]] && (( selection >= 1 && selection <= ${#candidates[@]} )); then
      printf '%s\n' "${candidates[selection-1]}"
      return 0
    fi
    warn "有効な番号を入力してください。"
  done
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --project)
        [[ $# -ge 2 ]] || error "--project には値が必要です。"
        PROJECT_NAME="$2"
        shift 2
        ;;
      --action)
        [[ $# -ge 2 ]] || error "--action には値が必要です。"
        ACTION="$2"
        case "$ACTION" in
          up|down|stop|start|restart|ps)
            ;;
          *)
            error "不明な action です: $ACTION"
            ;;
        esac
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        COMPOSE_ARGS+=("$1")
        shift
        ;;
    esac
  done
}

main() {
  parse_args "$@"
  ensure_docker_cli
  if ! docker_compose_ready; then
    error "docker compose が利用できません。Docker Desktop の Compose プラグインを確認してください。"
  fi

  if ! docker_engine_ready; then
    wait_for_docker_engine
  else
    log "Docker Engine は既に起動しています。"
  fi

  local project_dir
  project_dir="$(select_compose_project "$PROJECT_NAME")"
  log "docker compose $ACTION を実行します: $project_dir"

  (
    cd "$project_dir"
    if (( ${#COMPOSE_ARGS[@]} > 0 )); then
      docker compose "$ACTION" "${COMPOSE_ARGS[@]}"
    else
      docker compose "$ACTION"
    fi
  )
}

main "$@"
