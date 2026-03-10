#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "使い方: $0 <コンテナ内で実行したいコマンド...>"
  exit 1
fi

if [ -z "${TEAM_INFO_ROOT:-}" ]; then
  echo "TEAM_INFO_ROOT が未設定です。"
  echo "例: export TEAM_INFO_ROOT=/absolute/path/to/team-info"
  exit 1
fi

docker compose -f "$TEAM_INFO_ROOT/docker/team-info/docker-compose.yml" run --rm team-info "$@"
