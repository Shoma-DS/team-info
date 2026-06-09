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
& cutcli captions add $draftId --captions "@$cutcliDir\captions.json" --font-size 8 --bold --text-color "#FFFFFF"
Write-Host "CapCut draft ready: $draftId"
