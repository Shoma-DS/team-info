# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-2
- frame: 0 (0.0s)
- text_preview: 食べ られ ちゃ うた 女性 芸能
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:bottom|bg:1|stroke:0:0|multi:0|text:#e0c0c0|box:#402020

### style_02
- cut: 2-95
- frame: 60 (2.0s)
- text_preview: デー “A 食べ られ ちや 女性 芸能
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_02_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_02_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e0a080|box:#404020

### style_03
- cut: 99-206
- frame: 150 (5.0s)
- text_preview: EAH
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_03_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_03_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e080a0|box:#202020

### style_04
- cut: 206-280
- frame: 210 (7.0s)
- text_preview: フー oe ワウ レフ ピナ レス レス ビー スン ーー ‘a 絶対
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_04_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/食べちまった芸能人3選/subtitle_style_samples/style_04_crop.jpg
- heuristic_signature: zone:top|bg:0|stroke:0:0|multi:1|text:#e0e0e0|box:none
