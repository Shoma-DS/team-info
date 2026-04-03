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

## 共通構成ルール
- クリップが重ならないなら、素材種別ごとに 1 本のタイムライン駆動トラックを優先する
- 素材と音声は `staticFile("viral/[title]/...")` で参照する
- 字幕やフック描画は個別実装を増やさず、共通ロジックへ寄せる
- 挙動が同じならテンプレ専用コピーより共通コンポーネントを使う

## 共通確認
- 編集後に TypeScript チェックを行う
- composition id、duration、asset path を確認する
- 必要ならフック位置の still を出して確認する

## テンプレ差分
- `profile.yaml` を読む
- `phase_refs.remotion` があれば追加で読む
- 差分では見た目、モーション、テンポ、特殊描画ルールを調整する
