# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-60
- frame: 30 (1.0s)
- text_preview: NORA |/
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#80a080|box:#202020

### style_02
- cut: 118-142
- frame: 120 (4.0s)
- text_preview: =e 亜依
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_02_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_02_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e0ff20|box:#000000

### style_03
- cut: 142-174
- frame: 150 (5.0s)
- text_preview: ral
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_03_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_03_crop.jpg
- heuristic_signature: zone:bottom|bg:0|stroke:0:0|multi:0|text:#e0c0c0|box:none

### style_04
- cut: 174-249
- frame: 180 (6.0s)
- text_preview: あの 無邪気 笑顔
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_04_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_04_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:0|text:#e0e0e0|box:none

### style_05
- cut: 249-332
- frame: 330 (11.0s)
- text_preview: 原因
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_05_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_05_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#e0c0a0|box:#200000

### style_06
- cut: 332-397
- frame: 360 (12.0s)
- text_preview: Pye 相談
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_06_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_06_crop.jpg
- heuristic_signature: zone:middle|bg:1|stroke:1:4|multi:0|text:#ffffff|box:#002020

### style_07
- cut: 397-499
- frame: 420 (14.0s)
- text_preview: BG トヨ ツン 紹介 ay AN
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_07_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/アダルトアフィリ_20260312/他人のバナナが好きなアイドル/subtitle_style_samples/style_07_crop.jpg
- heuristic_signature: zone:bottom|bg:0|stroke:0:0|multi:1|text:#c0a080|box:none
