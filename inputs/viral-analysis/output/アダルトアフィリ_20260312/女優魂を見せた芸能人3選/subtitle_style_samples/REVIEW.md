# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-70
- frame: 60 (2.0s)
- text_preview: Hic Cz イカ Tz att こち
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:1|text:#ffc0c0|box:#200000

### style_02
- cut: 75-154
- frame: 150 (5.0s)
- text_preview: 1. 光輝
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_02_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_02_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e0ff20|box:#200000

### style_03
- cut: 179-294
- frame: 210 (7.0s)
- text_preview: 閉塞 漂う ah
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_03_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_03_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#ffe0c0|box:#200000

### style_04
- cut: 294-380
- frame: 330 (11.0s)
- text_preview: NN 池脇 演じ
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_04_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_04_crop.jpg
- heuristic_signature: zone:top|bg:1|stroke:1:4|multi:0|text:#e0c0c0|box:#402020

### style_05
- cut: 380-439
- frame: 420 (14.0s)
- text_preview: ce 誰か 必要
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_05_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/女優魂を見せた芸能人3選/subtitle_style_samples/style_05_crop.jpg
- heuristic_signature: zone:top|bg:1|stroke:1:4|multi:0|text:#808060|box:#202020
