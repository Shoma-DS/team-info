# Subtitle Style Review

AIエージェントは `subtitle_crop_path` を優先して見て、必要なら `full_frame_path` も確認する。
レビュー結果は `subtitle_style_template.json` に保存する。

## Samples

### style_01
- cut: 0-15192
- frame: 180 (6.0s)
- text_preview: 現場 実態 知ら 経営 管理 現場 実態 ほとん 把握 いな 現実 合わ いま
- full_frame_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【仕組みが終わってる】社員を消耗させ続ける会社の特徴9選/subtitle_style_samples/style_01_full.jpg
- subtitle_crop_path: /workspace/team-info/inputs/viral-analysis/output/転職横動画_20260404/【仕組みが終わってる】社員を消耗させ続ける会社の特徴9選/subtitle_style_samples/style_01_crop.jpg
- heuristic_signature: zone:middle|bg:0|stroke:0:0|multi:0|text:#ffffff|box:none
