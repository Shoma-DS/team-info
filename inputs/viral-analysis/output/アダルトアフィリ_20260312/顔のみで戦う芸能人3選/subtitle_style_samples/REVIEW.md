# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-75
- frame: 30 (1.0s)
- text_preview: NN、 ne att BEN 13 gh
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:0|text:#e0c0c0|box:none

### style_02
- cut: 80-144
- frame: 120 (4.0s)
- text_preview: 7K val
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_02_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_02_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:1|text:#e0a0a0|box:#202000

### style_03
- cut: 149-193
- frame: 150 (5.0s)
- text_preview: be 1. $y
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_03_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_03_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:1|text:#a08080|box:#202020

### style_04
- cut: 193-241
- frame: 210 (7.0s)
- text_preview: IN WY NN ケロ 絶対 セン NN NN SS NN [ZB
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_04_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/顔のみで戦う芸能人3選/subtitle_style_samples/style_04_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:0|text:#ffe0e0|box:none
