# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-25356
- frame: 180 (6.0s)
- text_preview: ける 想像 うこ ここ 働く 無理
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【ここじゃない感】「もう無理かも」と気づいた人の特徴9選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【ここじゃない感】「もう無理かも」と気づいた人の特徴9選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:1|text:#ffffff|box:none
