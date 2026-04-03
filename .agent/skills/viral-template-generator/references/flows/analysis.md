# analysis

## 目的
- 元のショート動画を動画ごとの `analysis.json` に変換する
- 後続フェーズで再利用できる分析バッチを作る

## 入力
- Default inbox: `inputs/viral-analysis/未分析/`
- Existing batches: `inputs/viral-analysis/output/`

## 出力
- `inputs/viral-analysis/output/[pattern]_YYYYMMDD/[video-title]/analysis.json`
- After success, move source videos to `inputs/viral-analysis/分析済み/[pattern]/`

## 開始前チェック
1. Scan `未分析/`, `分析済み/`, `output/`, and `Remotion/my-video/src/viral/`
2. Show the current state to the user
3. Confirm whether this is a new batch, overwrite, or resume path
4. Resolve the template profile before analysis if the user already knows it

## 基本実行
- 解析は `scripts/analyze_video.py` を優先する
- Python 実行は `team_info_runtime.py run-remotion-python --` を使う
- 長時間になりそうな解析は、コマンドをそのままユーザーへ渡して実行してもらう

## 出力確認
- 選んだ各動画に対して `analysis.json` が 1 つずつできていること
- 下流フェーズに入ったらバッチ名を途中で変えないこと
- 分かる場合は `tiktok` `shorts` `reels` のプラットフォーム情報を持たせること

## テンプレ差分
- `references/template-profiles/[template-id]/profile.yaml` を読む
- `phase_refs.analysis` があれば追加で読む
- 解析フロー自体は共通で済むことが多い
