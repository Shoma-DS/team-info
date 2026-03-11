---
name: remotion-template-sleep-travel-short-digest
description: sleep_travelチャンネルのshort_digestテンプレート専用編集スキル。短尺ダイジェスト構成に沿ってRemotionを編集する。
---

# sleep_travel short_digest 専用スキル

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` から絶対パスを組み立てる。

## 入力前提
- チャンネル: `sleep_travel`
- テンプレート: `short_digest`
- 親スキル `remotion-video-production` で選択済みであること。

## 参照ファイル
- `Remotion/my-video/public/assets/channels/sleep_travel/channel_info.md`
- `Remotion/my-video/public/assets/channels/sleep_travel/templates/short_digest.md`
- `Remotion/my-video/src/`

## 素材選択ルール（必須）
- 素材選択が必要な場合は、対象フォルダを走査して実在ファイルを番号付きで提示し、選択して確定する。
- 対象: 音声素材 / 台本 / 背景画像 / BGM / エフェクト設定（必要なもののみ）。
- 候補が0件なら、選択に進まず不足素材を明示する。
- カスタムエフェクトを使う場合は、その都度日本語名を付けてテンプレート保存する。
- エフェクトテンプレート保存先: `Remotion/my-video/public/assets/channels/sleep_travel/effects/templates/`

## Remotion実装ルール（必須）
- 背景画像、差し込み画像、効果音、字幕など、同じ種類で時系列が重ならない素材は、種類ごとに `<Sequence>` を1本へ統合する。
- 同種素材を `map(...<Sequence>...)` で並べず、タイムライン配列と現在フレームからアクティブ素材を切り替える。
- 複数 `<Sequence>` を分けるのは、同種素材の同時表示やクロスフェードなど、時間重複が実際に必要な場合だけに限定する。

## 編集フロー
1. テンプレートのシーン構成（フック -> 本編3セクション -> まとめ）を読み込む。
2. 必要素材がある場合は、候補ファイルを提示して確定する。
3. エフェクト設定が既存テンプレートにない場合は、適切な日本語名で新規テンプレートを保存する。
4. `Remotion/my-video/src/` に短尺向けコンポーネントを実装または更新する。
5. 必要なら `Remotion/my-video/src/Root.tsx` にCompositionを追加する。
6. 次を満たすよう調整する。
- 導入を短く明確にする
- 1セクション1要点
- 可読性を優先
- 非重複な同種レイヤーは `<Sequence>` 1本で管理する
7. `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run lint` を実行する。
8. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion render ... --output="$TEAM_INFO_ROOT/outputs/sleep_travel/renders/..."` コマンドを提示する。
- レンダリング前の確認文言は必ず `出力しますか？書き出しますか？` を使う。
- 過去ターンで承認があっても、レンダリング直前に毎回確認する。
- レンダリング出力先は必ず `outputs/sleep_travel/renders/` を使う。
9. 実施内容、編集ファイル、lint結果を報告する。
