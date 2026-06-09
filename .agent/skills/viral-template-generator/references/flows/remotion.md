# remotion

## 目的
- ショート動画テンプレ用の Remotion Composition を作る、または更新する

## 入力
- `subtitles.json`
- final narration audio
- prepared `materials/`
- template profile overrides

## 標準出力
- `Remotion/my-video/src/viral/...`
- `Remotion/my-video/public/viral/...`
- `Root.tsx` composition registration when needed
- `outputs/capcut/...` after CapCut sync

## 共通構成ルール
- クリップが重ならないなら、素材種別ごとに 1 本のタイムライン駆動トラックを優先する
- 素材と音声は `staticFile("viral/[title]/...")` で参照する
- 字幕やフック描画は個別実装を増やさず、共通ロジックへ寄せる
- 挙動が同じならテンプレ専用コピーより共通コンポーネントを使う
- 新しいショート動画では、過去ショートの画像素材パスを参照しない。`staticFile("viral/[old-title]/...")`、過去作の `materials/`、過去作の画像 import が残っていたら必ず新規素材へ差し替える
- 既存コンポーネントを土台にする場合も、レイアウト定数とモーションだけを参考にし、画像配列は今回の動画専用 `materials/` から組み直す

## 共通確認
- 編集後に TypeScript チェックを行う
- composition id、duration、asset path を確認する
- 必要ならフック位置の still を出して確認する
- asset path 確認では、過去ショートの動画フォルダ名や画像ファイル名が残っていないことを確認する
- Remotion組み込み後に `npm --prefix "$env:TEAM_INFO_ROOT\Remotion\my-video" run sync:capcut` を実行し、CapCutパッケージ、SRT、timeline、cutcli用JSONが生成されたか確認する
- `cutcli` 未導入でドラフト生成がスキップされた場合は、生成用ファイルまで作成済みとして報告する

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.remotion` があれば追加で読む
- 差分では見た目、モーション、テンポ、特殊描画ルールを調整する
