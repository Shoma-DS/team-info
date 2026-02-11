#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 <output_root>"
  exit 1
fi

OUTPUT_ROOT="$1"
mkdir -p "$OUTPUT_ROOT"

for i in $(seq -w 1 12); do
  FILE="$OUTPUT_ROOT/post${i}.md"
  if [ ! -f "$FILE" ]; then
    cat > "$FILE" <<'TPL'
# タイトル

## 本文

## 仕事内容詳細

## 募集概要
- 職種:
- 雇用形態:
- 勤務地:
- 勤務時間:
- 給与:
- 休日:
- 応募条件:

## 応募導線
気になる方は公式LINEからご連絡ください。  
【公式LINEURL】
TPL
  fi
done

echo "Created 12 post files under: $OUTPUT_ROOT"
