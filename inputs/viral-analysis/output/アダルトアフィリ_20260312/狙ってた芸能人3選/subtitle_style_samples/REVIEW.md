# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-90
- frame: 60 (2.0s)
- text_preview: -@ つぐ Ny 女性 芸能
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:1|text:#ffe0e0|box:#202020

### style_02
- cut: 90-91
- frame: 90 (3.0s)
- text_preview: ヤリ 女性 芸能
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_02_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_02_crop.jpg
- heuristic_signature: zone:bottom|bg:1|stroke:1:4|multi:1|text:#ffe0e0|box:#200000

### style_03
- cut: 150-151
- frame: 150 (5.0s)
- text_preview: i= FA 代表
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_03_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_03_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e080a0|box:#200000

### style_04
- cut: 151-188
- frame: 180 (6.0s)
- text_preview: 綾子
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_04_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_04_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e0ff20|box:#000000

### style_05
- cut: 188-294
- frame: 240 (8.0s)
- text_preview: 実力
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_05_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_05_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:0|text:#ffffff|box:none

### style_06
- cut: 294-429
- frame: 330 (11.0s)
- text_preview: 評判 id
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_06_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/狙ってた芸能人3選/subtitle_style_samples/style_06_crop.jpg
- heuristic_signature: zone:bottom|bg:1|stroke:1:4|multi:0|text:#c0a0c0|box:#200000
