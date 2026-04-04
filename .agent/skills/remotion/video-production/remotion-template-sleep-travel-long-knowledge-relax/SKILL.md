---
name: remotion-template-sleep-travel-long-knowledge-relax
description: sleep_travelチャンネルのlong_knowledge_relaxテンプレート専用編集スキル。長尺睡眠導入の構成に沿ってRemotionを編集する。
---

# sleep_travel long_knowledge_relax 専用スキル

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` から絶対パスを組み立てる。

## 入力前提
- チャンネル: `sleep_travel`
- テンプレート: `long_knowledge_relax`
- 親スキル `remotion-video-production` で選択済みであること。

## 参照ファイル
- `Remotion/my-video/public/assets/channels/sleep_travel/channel_info.md`
- `Remotion/my-video/public/assets/channels/sleep_travel/templates/long_knowledge_relax.md`
- `Remotion/my-video/src/`

## 素材参照先
- 台本: `Remotion/scripts/voice_scripts/`
- 音声: `outputs/sleep_travel/audio/`
- 背景画像: `Remotion/my-video/public/assets/channels/sleep_travel/backgrounds/`
- BGM: `Remotion/my-video/public/assets/channels/sleep_travel/bgm/`
- エフェクトテンプレート: `Remotion/my-video/public/assets/channels/sleep_travel/effects/templates/`

## 素材選択ルール（必須）
- 素材選択時は、対象フォルダを走査して「実在する候補ファイル」を番号付きで提示する。
- 「音声素材 / 台本 / 背景画像 / BGM / エフェクト設定」の5項目を1つずつ順番に確定する。
- 拡張子フィルタ:
- 音声素材: `.mp3`
- 台本: `.md` `.txt`
- 背景画像: `.png` `.jpg` `.jpeg`
- BGM: `.mp3`
- 候補0件の項目があれば、先に不足を報告して補充を依頼する。
- カスタムエフェクトを新規作成した場合は、都度「日本語名」を付けてテンプレートとして保存する。
- エフェクトテンプレート保存先: `Remotion/my-video/public/assets/channels/sleep_travel/effects/templates/`
- 保存時は、次回再利用できるよう目的・適用シーン・主要パラメータを残す。

## Remotion実装ルール（必須）
- 背景画像差し替え、補助画像、効果音、字幕など、同じ種類で区間が重ならない素材は、種類ごとに `<Sequence>` を1本へ統合する。
- 同種素材を `map(...<Sequence>...)` で量産せず、タイムライン配列から現在フレームに対応する素材を選んで描画・再生する。
- BGM だけは例外として `<Loop>` 1つで管理してよいが、`<Sequence>` を分割して疑似ループを組まない。
- クロスフェードなど同種素材の重なりが本当に必要な場面を除き、同種レイヤーを複数本に分けない。
- 生成・更新する **すべての `<Sequence>` に `name` を付ける。** 例: `背景画像`, `補助画像`, `字幕`, `BGM`, `音声 ナレーション`。
- 字幕の折り返しは `Remotion/my-video/src/textLayout.ts` の BudouX ベース共通ヘルパーに寄せる。SleepTravelLong 側で独自の改行ロジックを増やさない。

## 編集フロー
1. テンプレート定義を読み、シーン構成と実装仕様を確認する。
2. 素材を必ず1つずつ確認して確定する。
- 音声素材
- 台本
- 背景画像
- BGM
- エフェクト設定
3. エフェクト設定が既存テンプレートにない場合は、適切な日本語名で新規テンプレートを保存する。
4. `Remotion/my-video/src/` に長尺向けコンポーネントを実装または更新する。
5. 次を必須で満たす。
- 背景画像をベース表示
- 音声主役、BGMは控えめ音量
- BGMをシームレスループ（`<Loop durationInFrames={bgmSegmentFrames} times={loopCount}>` を1つ使う）
  - `loopCount = Math.ceil(durationInFrames / bgmSegmentFrames) + 1` で必ず動画の最後までカバー
  - **`times` を省略すると音声がレンダリングされない**（Remotion 仕様）ので必ず指定する
- BGMループは必ず `<Sequence>` を複数生成するパターンではなく `<Loop>` 1つに統一する
- 背景画像や字幕など非重複な同種レイヤーは `<Sequence>` 1本で管理する
- 各 `<Sequence>` には役割が一目で分かる `name` を付ける
- 字幕を音声進行に合わせる
- 字幕の自然な改行は BudouX ベースの共通ヘルパーで整形する
- 字幕をフェードイン/フェードアウト
- 白線のシンプルなオーディオスペクトラム表示
6. 必要なら `Remotion/my-video/src/Root.tsx` にCompositionを追加する。
7. `npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run lint` を実行する。
8. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion render ... --output="$TEAM_INFO_ROOT/outputs/sleep_travel/renders/..."` コマンドを提示する。
- レンダリング前の確認文言は必ず `出力しますか？書き出しますか？` を使う。
- 過去ターンで承認があっても、レンダリング直前に毎回確認する。
- レンダリング出力先は必ず `outputs/sleep_travel/renders/` を使う。
- レンダリング完了後に Step 9 のコマンドも提示する。
9. レンダリング完了後、以下のコマンドで Google Drive にコピーする（コマンドをユーザーに提示するだけ・自分では実行しない）：
   ```bash
   rclone copy "$TEAM_INFO_ROOT/outputs/sleep_travel/renders/[ファイル名].mp4" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/寝ながらトラベル/" --progress
   ```
   - rclone が未設定の場合は `.agent/skills/common/gdrive-copy/SKILL.md` の初回セットアップ手順を案内する。
10. 実施内容、編集ファイル、lint結果を報告する。
