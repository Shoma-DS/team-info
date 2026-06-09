#!/usr/bin/env bash
# This file creates a CapCut draft from the exported Remotion package.
set -euo pipefail
CUTCLI_DIR="C:/Users/abc_p/OneDrive/デスクトップ/teaminfo/outputs/capcut/会社に見切りをつける直前の人の特徴9選_20260412/cutcli"
DRAFT_JSON="$(cutcli draft create --width 1280 --height 720)"
DRAFT_ID="$(node -e 'let s="";process.stdin.on("data",d=>s+=d);process.stdin.on("end",()=>console.log(JSON.parse(s).draftId))' <<< "$DRAFT_JSON")"
echo "Created draft: $DRAFT_ID"
cutcli images add "$DRAFT_ID" --image-infos "@$CUTCLI_DIR/images.json"
cutcli audios add "$DRAFT_ID" --audio-infos "@$CUTCLI_DIR/audios.json"
cutcli captions add "$DRAFT_ID" --captions "@$CUTCLI_DIR/captions.json" --font "Yu Gothic UI" --font-size 8 --bold --text-color "#FFFFFF" --border-color "#000000" --border-width 5 --alignment 0 --transform-x 0 --transform-y -0.72 --line-spacing 0.85
echo "CapCut draft ready: $DRAFT_ID"
