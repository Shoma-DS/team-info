#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <composition-id> <output-file-name-or-path.mp4>"
  echo "Example: $0 AcoRiel-SAY-YES-Lyric say-yes.mp4"
  exit 1
fi

COMPOSITION_ID="$1"
OUTPUT_NAME="$2"

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$ROOT_DIR/my-video"
UNIFIED_OUTPUT_ROOT="$ROOT_DIR/../outputs"

if [[ "$COMPOSITION_ID" == AcoRiel* ]]; then
  CATEGORY_DIR="acoriel/renders"
elif [[ "$COMPOSITION_ID" == SleepTravel* ]]; then
  CATEGORY_DIR="sleep_travel/renders"
elif [[ "$COMPOSITION_ID" == Jmty* ]]; then
  CATEGORY_DIR="jmty/renders"
else
  CATEGORY_DIR="common/renders"
fi

UNIFIED_OUTPUT_DIR="$UNIFIED_OUTPUT_ROOT/$CATEGORY_DIR"

mkdir -p "$UNIFIED_OUTPUT_DIR"

if [[ "$OUTPUT_NAME" != *.mp4 ]]; then
  OUTPUT_NAME="${OUTPUT_NAME}.mp4"
fi

OUTPUT_PATH="$UNIFIED_OUTPUT_DIR/$(basename "$OUTPUT_NAME")"

cd "$PROJECT_DIR"
npx remotion render src/index.ts "$COMPOSITION_ID" "$OUTPUT_PATH"
