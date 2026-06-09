# This file creates a CapCut draft from the exported Remotion package.
# Run it after installing cutcli and confirming CapCut's draft path.
$ErrorActionPreference = "Stop"
$cutcliDir = "C:\Users\abc_p\OneDrive\デスクトップ\teaminfo\outputs\capcut\TenshokuShort20260602\cutcli"
$draftJson = & cutcli draft create --width 1080 --height 1920
$draft = $draftJson | ConvertFrom-Json
$draftId = $draft.draftId
Write-Host "Created draft: $draftId"
& cutcli images add $draftId --image-infos "@$cutcliDir\images.json"
& cutcli audios add $draftId --audio-infos "@$cutcliDir\audios.json"
& cutcli captions add $draftId --captions "@$cutcliDir\captions.json" --font "Yu Gothic UI" --font-size 10 --bold --text-color "#FFFFFF" --border-color "#000000" --border-width 5 --alignment 0 --transform-x 0 --transform-y -0.72 --line-spacing 0.85
Write-Host "CapCut draft ready: $draftId"
