#!/usr/bin/env bash
set -euo pipefail

shared_repo_path="${1:-}"

if [ -z "$shared_repo_path" ]; then
  echo "usage: sync_shared_agent_repo.sh /absolute/path/to/shared-agent-assets"
  exit 64
fi

if [ ! -d "$shared_repo_path/.git" ]; then
  echo "⚠ shared agent repo not found"
  exit 0
fi

if ! git -C "$shared_repo_path" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "⚠ shared agent repo has no commits yet"
  exit 0
fi

if ! git -C "$shared_repo_path" diff --quiet || ! git -C "$shared_repo_path" diff --cached --quiet; then
  echo "⚠ shared agent repo has local changes"
  exit 0
fi

if ! git -C "$shared_repo_path" fetch --quiet >/dev/null 2>&1; then
  echo "⚠ shared agent repo fetch failed"
  exit 0
fi

local_head="$(git -C "$shared_repo_path" rev-parse HEAD)"
upstream_head="$(git -C "$shared_repo_path" rev-parse @{u} 2>/dev/null || true)"

if [ -z "$upstream_head" ]; then
  echo "⚠ shared agent repo upstream is not configured"
  exit 0
fi

if [ "$local_head" = "$upstream_head" ]; then
  echo "✓ shared agent assets are up to date"
  exit 0
fi

if git -C "$shared_repo_path" pull --ff-only --quiet >/dev/null 2>&1; then
  echo "✓ shared agent assets updated"
  exit 0
fi

echo "⚠ shared agent repo pull failed"
exit 0
