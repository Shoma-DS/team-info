#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIFY_DIR="${ROOT_DIR}/dify"

if [[ ! -d "${DIFY_DIR}" ]]; then
  echo "[info] Cloning Dify repository into ${DIFY_DIR}"
  git clone https://github.com/langgenius/dify.git "${DIFY_DIR}"
else
  echo "[info] Existing Dify repository found: ${DIFY_DIR}"
fi

cd "${DIFY_DIR}/docker"

if [[ ! -f .env ]]; then
  echo "[info] Creating .env from .env.example"
  cp .env.example .env
fi

echo "[info] Starting Dify with docker compose"
docker compose up -d

echo "[done] Dify is starting."
echo "[hint] Open http://localhost:3000 after containers become healthy."
