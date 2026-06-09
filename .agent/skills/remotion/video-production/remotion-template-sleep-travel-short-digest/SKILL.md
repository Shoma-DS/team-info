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

## ショート画像素材の新規作成ルール（必須）
- 新しいショート動画では、過去ショートで使った画像ファイルを選択候補にしない。過去作フォルダからのコピー、同じ生成画像セットの再利用、過去作の staticFile 参照の残置は禁止する。
- 背景画像・差し込み画像は、台本ごとに新しく画像生成するか、いらすとや等のイラスト素材、または利用条件を満たすフリー素材サイトから新規取得する。
- 既存ショートを参考にしてよいのは、画面内のサイズ感、人物/物の置き位置、字幕との距離、ズーム量、切り替えテンポなどの編集設計だけ。
- 実装前に、フック・各セクション・CTAごとの画像計画を作り、各画像の取得方法と保存先を決めてからコードへ反映する。
- 素材保存先は動画単位の専用フォルダにする。例: `Remotion/my-video/public/assets/channels/sleep_travel/short_digest/<project_id>/images/`
- 最終確認では、画像配列・import・staticFile の参照先を見て、過去ショートの素材パスが残っていないことを確認する。

## Remotion実装ルール（必須）
- 背景画像、差し込み画像、効果音、字幕など、同じ種類で時系列が重ならない素材は、種類ごとに `<Sequence>` を1本へ統合する。
- 同種素材を `map(...<Sequence>...)` で並べず、タイムライン配列と現在フレームからアクティブ素材を切り替える。
- 複数 `<Sequence>` を分けるのは、同種素材の同時表示やクロスフェードなど、時間重複が実際に必要な場合だけに限定する。
- 生成・更新する **すべての `<Sequence>` に `name` を付ける。** 例: `背景画像`, `差し込み画像`, `字幕`, `効果音`, `音声 ナレーション`。
- 字幕の自然な改行は `Remotion/my-video/src/textLayout.ts` の BudouX ベース共通ヘルパーに寄せる。short_digest 側で独自の改行ロジックを増やさない。

## 編集フロー
1. テンプレートのシーン構成（フック -> 本編3セクション -> まとめ）を読み込む。
2. 台本ごとの画像計画を作り、過去作流用なしで新規画像を生成または取得する。
3. 必要素材がある場合は、候補ファイルを提示して確定する。ただし過去ショートの画像素材は候補から除外する。
4. エフェクト設定が既存テンプレートにない場合は、適切な日本語名で新規テンプレートを保存する。
5. `Remotion/my-video/src/` に短尺向けコンポーネントを実装または更新する。
6. 必要なら `Remotion/my-video/src/Root.tsx` にCompositionを追加する。
7. 次を満たすよう調整する。
- 導入を短く明確にする
- 1セクション1要点
- 可読性を優先
- 非重複な同種レイヤーは `<Sequence>` 1本で管理する
- 各 `<Sequence>` には役割が一目で分かる `name` を付ける
- テロップの折り返しは BudouX ベースの共通ヘルパーで整形する
8. 画像素材の参照先を確認し、過去ショートの画像パスが残っていないことを確認する。
9. `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run lint` を実行する。
10. CapCut連携を自動同期する。
   ```powershell
   npm --prefix "$env:TEAM_INFO_ROOT\Remotion\my-video" run sync:capcut
   ```
   - `outputs/capcut/` に対象パッケージ、`captions.srt`、`timeline.json`、cutcli用JSONが出たか確認する。
   - `cutcli` 未導入でドラフト生成がスキップされた場合は、生成用ファイルまで作成済みとして報告する。
11. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion render ... --output="$TEAM_INFO_ROOT/outputs/sleep_travel/renders/..."` コマンドを提示する。
- レンダリング前の確認文言は必ず `出力しますか？書き出しますか？` を使う。
- 過去ターンで承認があっても、レンダリング直前に毎回確認する。
- レンダリング出力先は必ず `outputs/sleep_travel/renders/` を使う。
- レンダリング完了後に Step 12 のコマンドも提示する。
12. レンダリング完了後、以下のコマンドで Google Drive にコピーする（コマンドをユーザーに提示するだけ・自分では実行しない）：
   ```bash
   rclone copy "$TEAM_INFO_ROOT/outputs/sleep_travel/renders/[ファイル名].mp4" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/寝ながらトラベル/" --progress
   ```
   - rclone が未設定の場合は `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。
13. 実施内容、編集ファイル、画像素材の新規作成/取得元、過去作流用なしの確認結果、lint結果、CapCut同期結果を報告する。
