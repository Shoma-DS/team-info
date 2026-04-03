# パイプライン概要

## 役割
- `viral-template-generator` はショート動画解析とテンプレ生成の入口スキル
- 本体の `SKILL.md` は薄く保ち、詳細は flow に分けて読む
- テンプレ固有の違いは `references/template-profiles/` に置く

## 標準フロー
1. 元動画を `analysis.json` へ変換する
2. 分析バッチを統合して `viral_patterns.md` を作る
3. テーマを決めて `script.md` を作る
4. `script_hiragana.md`、`subtitles.json`、音声を作る
5. `materials/` を準備する
6. Remotion 用ファイルを組み込む
7. 必要なら jet cut、alignment、render を行う

## 共通パス
- `inputs/viral-analysis/未分析/`
- `inputs/viral-analysis/分析済み/`
- `inputs/viral-analysis/output/`
- `Remotion/my-video/public/viral/`
- `Remotion/my-video/src/viral/`

## 読み込みルール
1. まず `SKILL.md` を読む
2. 今のフェーズに対応する `references/flows/` のファイルを読む
3. `references/template-profiles/[template-id]/profile.yaml` を読む
4. そのフェーズ専用の override があるときだけ追加で読む

## テンプレ継承
- `standard-short` を標準プロファイルとして使う
- template profile には差分だけを書く
- override がないフェーズは共通 flow をそのまま使う
