#!/usr/bin/env bash
set -euo pipefail

DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${DOCKER_DIR}/.." && pwd)"
DIFY_DIR="${DOCKER_DIR}/dify"

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

echo "[info] Starting Dify with common Docker launcher"
bash "${ROOT_DIR}/run.sh" --project dify -d

echo "[done] Dify is starting."
echo "[hint] Open http://localhost:3000 after containers become healthy."
