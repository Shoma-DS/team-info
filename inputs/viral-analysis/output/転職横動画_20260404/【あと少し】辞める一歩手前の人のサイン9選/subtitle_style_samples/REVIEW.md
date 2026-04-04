# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-18129
- frame: 150 (5.0s)
- text_preview: 愚痴 減っ 4/ 辞め 手前 いる ある ほとん わな
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【あと少し】辞める一歩手前の人のサイン9選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【あと少し】辞める一歩手前の人のサイン9選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:0|text:#ffffff|box:none
