#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 <composition-id> <output-file-name-or-path.mp4> [--props <json-or-json-file>]"
  echo "       $0"
  echo "Example: $0 AcoRiel-SAY-YES-Lyric say-yes.mp4"
  echo "Example: $0 Viral-Studio-Template viral-variant.mp4 --props /abs/path/to/viral-props.json"
  echo ""
  echo "引数なしで実行すると、Remotion標準のComposition選択画面を起動します。"
}

resolve_path() {
  local input_path="$1"
  local input_dir
  input_dir="$(cd "$(dirname "$input_path")" && pwd)"
  echo "$input_dir/$(basename "$input_path")"
}

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_DIR="$ROOT_DIR/my-video"
UNIFIED_OUTPUT_ROOT="$ROOT_DIR/../outputs"
STABLE_RENDER_ARGS=(
  --concurrency=1
  --timeout=900000
  --offthreadvideo-video-threads=1
  --media-cache-size-in-bytes=1073741824
)
MAX_RENDER_ATTEMPTS="${RENDA_RENDER_ATTEMPTS:-2}"

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

category_for_composition() {
  local composition_id="$1"
  if [[ "$composition_id" == AcoRiel* ]]; then
    echo "acoriel/renders"
  elif [[ "$composition_id" == SleepTravel* ]]; then
    echo "sleep_travel/renders"
  elif [[ "$composition_id" == Jmty* ]]; then
    echo "jmty/renders"
  elif [[ "$composition_id" == Viral* || "$composition_id" == Tenshoku* || "$composition_id" == AdultAffiliate* ]]; then
    echo "viral/renders"
  else
    echo "common/renders"
  fi
}

run_render_with_retry() {
  local attempt=1
  while true; do
    if npx remotion render "$@"; then
      return 0
    fi

    if [ "$attempt" -ge "$MAX_RENDER_ATTEMPTS" ]; then
      return 1
    fi

    echo ""
    echo "レンダリングに失敗しました。読み込み揺れ対策として再試行します ($((attempt + 1))/$MAX_RENDER_ATTEMPTS)..."
    attempt=$((attempt + 1))
    sleep 3
  done
}

move_default_render_to_outputs() {
  local rendered_file="$1"
  local composition_id
  local category_dir
  local output_dir
  local output_path

  if [ -z "$rendered_file" ] || [ ! -f "$rendered_file" ]; then
    return 0
  fi

  composition_id="$(basename "$rendered_file" .mp4)"
  category_dir="$(category_for_composition "$composition_id")"
  output_dir="$UNIFIED_OUTPUT_ROOT/$category_dir"
  output_path="$output_dir/$(basename "$rendered_file")"

  mkdir -p "$output_dir"
  mv "$rendered_file" "$output_path"
  echo ""
  echo "出力先を統一しました: $output_path"
  python3 "$ROOT_DIR/scripts/post_render_upload_prompt.py" --file "$output_path"
}

latest_default_render_after_marker() {
  local marker="$1"
  if [ ! -d "$PROJECT_DIR/out" ]; then
    return 0
  fi

  find "$PROJECT_DIR/out" -type f -name "*.mp4" -newer "$marker" -print |
    sort |
    tail -n 1
}

if [ "$#" -eq 0 ]; then
  marker="$(mktemp)"
  touch "$marker"
  cd "$PROJECT_DIR"
  run_render_with_retry src/index.ts "${STABLE_RENDER_ARGS[@]}"
  rendered_file="$(latest_default_render_after_marker "$marker")"
  rm -f "$marker"
  move_default_render_to_outputs "$rendered_file"
  exit 0
elif [ "$#" -eq 1 ]; then
  COMPOSITION_ID="$1"
  CATEGORY_DIR="$(category_for_composition "$COMPOSITION_ID")"
  UNIFIED_OUTPUT_DIR="$UNIFIED_OUTPUT_ROOT/$CATEGORY_DIR"
  OUTPUT_PATH="$UNIFIED_OUTPUT_DIR/$COMPOSITION_ID.mp4"
  mkdir -p "$UNIFIED_OUTPUT_DIR"
  cd "$PROJECT_DIR"
  run_render_with_retry src/index.ts "$COMPOSITION_ID" "$OUTPUT_PATH" "${STABLE_RENDER_ARGS[@]}"
  echo ""
  python3 "$ROOT_DIR/scripts/post_render_upload_prompt.py" --file "$OUTPUT_PATH"
  exit 0
else
  COMPOSITION_ID="$1"
  shift
  OUTPUT_NAME="$1"
  shift
fi

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

CATEGORY_DIR="$(category_for_composition "$COMPOSITION_ID")"

UNIFIED_OUTPUT_DIR="$UNIFIED_OUTPUT_ROOT/$CATEGORY_DIR"

mkdir -p "$UNIFIED_OUTPUT_DIR"

if [[ "$OUTPUT_NAME" != *.mp4 ]]; then
  OUTPUT_NAME="${OUTPUT_NAME}.mp4"
fi

OUTPUT_PATH="$UNIFIED_OUTPUT_DIR/$(basename "$OUTPUT_NAME")"

cd "$PROJECT_DIR"
run_render_with_retry src/index.ts "$COMPOSITION_ID" "$OUTPUT_PATH" "${STABLE_RENDER_ARGS[@]}" ${PROPS_ARG[@]+"${PROPS_ARG[@]}"}

# -----------------------------------------------------------------------------
# YouTube Upload Prompt (Optional)
# -----------------------------------------------------------------------------
echo ""
python3 "$ROOT_DIR/scripts/post_render_upload_prompt.py" --file "$OUTPUT_PATH"
