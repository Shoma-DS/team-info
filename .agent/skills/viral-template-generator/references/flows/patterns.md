# patterns

## 目的
- 複数の `analysis.json` を統合し、再利用しやすいパターン要約にする
- 後続フェーズが参照しやすい `viral_patterns.md` を作る

## 入力
- One batch folder under `inputs/viral-analysis/output/[pattern]_YYYYMMDD/`
- All nested `analysis.json` files in that batch

## 出力
- `viral_patterns.md`
- Material-count guidance for the next phase

## 標準セクション
- Basic stats
- Timing structure
- Hook tendencies
- Pattern interrupts
- Subtitle tendencies
- Script structure guidance
- Material count estimate
- Creative direction
- Optional BGM / SFX notes when they are clear in source analyses

## まとめ方のルール
- 単発の外れ値より中央値と多数派を優先する
- 再現性に影響する例外だけを明示する
- 字幕スタイルはスクショレビューや承認済みテンプレがない限り暫定扱いにする
- 生データの羅列ではなく、次工程で使える結論を書く

## テンプレ差分
- 先に `profile.yaml` を読む
- `phase_refs.patterns` があれば追加で読む
- 差分は解釈や重み付けに寄せ、統計フォーマットを大きく崩さない
