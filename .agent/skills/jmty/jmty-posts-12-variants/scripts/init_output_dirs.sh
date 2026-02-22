#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 <output_root>"
  exit 1
fi

OUTPUT_ROOT="$1"
mkdir -p "$OUTPUT_ROOT"

for i in $(seq -w 1 12); do
  DIR="$OUTPUT_ROOT/${i}_post"
  mkdir -p "$DIR"
  if [ ! -f "$DIR/post.md" ]; then
    cat > "$DIR/post.md" <<'EOF'
# タイトル

## 本文

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

## 注意事項
- 会社名は匿名表現にする（例: 大手製造業、地域密着の物流会社）
EOF
  fi
done

echo "Created 12 post folders under: $OUTPUT_ROOT"
