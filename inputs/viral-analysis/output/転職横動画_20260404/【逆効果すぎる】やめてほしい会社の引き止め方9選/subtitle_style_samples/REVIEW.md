# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-19745
- frame: 150 (5.0s)
- text_preview: ①「 辞め られ 困る くる
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【逆効果すぎる】やめてほしい会社の引き止め方9選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【逆効果すぎる】やめてほしい会社の引き止め方9選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:top|bg:1|stroke:0:0|multi:0|text:#ffffff|box:#000000
