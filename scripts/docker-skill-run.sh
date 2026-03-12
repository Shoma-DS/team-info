#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "使い方: $0 <コンテナ内で実行したいコマンド...>"
  exit 1
fi

if [ -z "${TEAM_INFO_ROOT:-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  TEAM_INFO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

docker compose -f "$TEAM_INFO_ROOT/docker/team-info/docker-compose.yml" run --rm team-info "$@"
