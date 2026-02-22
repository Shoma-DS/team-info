#!/usr/bin/env bash
set -euo pipefail

SRC_ROOT="outputs/jmty_posts"
SRC_FACTORY="$SRC_ROOT/factory"
SRC_REMOTE="$SRC_ROOT/remote"

DEFAULT_DEST_ROOT="/Users/deguchishouma/Library/CloudStorage/GoogleDrive-syouma1674@gmail.com/マイドライブ/team-info/outputs/jmty_posts"
DEST_ROOT="${1:-$DEFAULT_DEST_ROOT}"

if [ ! -d "$SRC_FACTORY" ]; then
  echo "[ERROR] source not found: $SRC_FACTORY"
  exit 1
fi

if [ ! -d "$SRC_REMOTE" ]; then
  echo "[ERROR] source not found: $SRC_REMOTE"
  exit 1
fi

mkdir -p "$DEST_ROOT"

# overwrite sync (including delete removed files)
rsync -a --delete "$SRC_FACTORY/" "$DEST_ROOT/factory/"
rsync -a --delete "$SRC_REMOTE/" "$DEST_ROOT/remote/"

echo "Synced successfully"
echo "- source: $SRC_FACTORY -> $DEST_ROOT/factory"
echo "- source: $SRC_REMOTE -> $DEST_ROOT/remote"
