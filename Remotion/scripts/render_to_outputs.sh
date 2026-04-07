#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <composition-id> <output-file-name-or-path.mp4> [--props <json-or-json-file>]"
  echo "Example: $0 AcoRiel-SAY-YES-Lyric say-yes.mp4"
  echo "Example: $0 Viral-Studio-Template viral-variant.mp4 --props /abs/path/to/viral-props.json"
}

resolve_path() {
  local input_path="$1"
  local input_dir
  input_dir="$(cd "$(dirname "$input_path")" && pwd)"
  echo "$input_dir/$(basename "$input_path")"
}

if [ "$#" -lt 2 ]; then
  usage
  exit 1
fi

COMPOSITION_ID="$1"
shift
OUTPUT_NAME="$1"
shift

PROPS_ARG=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --props)
      if [ "$#" -lt 2 ]; then
        echo "Error: --props には JSON 文字列または JSON ファイルのパスが必要です"
        usage
        exit 1
      fi
      if [ -f "$2" ]; then
        PROPS_ARG=(--props "$(resolve_path "$2")")
      else
        PROPS_ARG=(--props "$2")
      fi
      shift 2
      ;;
    --props=*)
      PROPS_VALUE="${1#--props=}"
      if [ -f "$PROPS_VALUE" ]; then
        PROPS_ARG=(--props "$(resolve_path "$PROPS_VALUE")")
      else
        PROPS_ARG=(--props "$PROPS_VALUE")
      fi
      shift
      ;;
    *)
      echo "Error: Unknown argument '$1'"
      usage
      exit 1
      ;;
  esac
done

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$ROOT_DIR/my-video"
UNIFIED_OUTPUT_ROOT="$ROOT_DIR/../outputs"

if [[ "$COMPOSITION_ID" == AcoRiel* ]]; then
  CATEGORY_DIR="acoriel/renders"
elif [[ "$COMPOSITION_ID" == SleepTravel* ]]; then
  CATEGORY_DIR="sleep_travel/renders"
elif [[ "$COMPOSITION_ID" == Jmty* ]]; then
  CATEGORY_DIR="jmty/renders"
elif [[ "$COMPOSITION_ID" == Viral* ]]; then
  CATEGORY_DIR="viral/renders"
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
npx remotion render src/index.ts "$COMPOSITION_ID" "$OUTPUT_PATH" ${PROPS_ARG[@]+"${PROPS_ARG[@]}"}

# -----------------------------------------------------------------------------
# YouTube Upload Prompt (Optional)
# -----------------------------------------------------------------------------
echo ""
python3 "$ROOT_DIR/scripts/post_render_upload_prompt.py" --file "$OUTPUT_PATH"
