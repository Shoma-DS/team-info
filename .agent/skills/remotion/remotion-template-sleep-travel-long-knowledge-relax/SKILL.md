---
name: remotion-template-sleep-travel-long-knowledge-relax
description: sleep_travelチャンネルのlong_knowledge_relaxテンプレート専用編集スキル。長尺睡眠導入の構成に沿ってRemotionを編集する。
---

# sleep_travel long_knowledge_relax 専用スキル

## 入力前提
- チャンネル: `sleep_travel`
- テンプレート: `long_knowledge_relax`
- 親スキル `remotion-video-production` で選択済みであること。

## 参照ファイル
- `Remotion/video_resources/channels/sleep_travel/channel_info.md`
- `Remotion/video_resources/channels/sleep_travel/templates/long_knowledge_relax.md`
- `Remotion/my-video/src/`

## 素材参照先
- 台本: `Remotion/scripts/voice_scripts/`
- 音声: `Remotion/output/audio/`
- 背景画像: `Remotion/video_resources/channels/sleep_travel/assets/backgrounds/`
- BGM: `Remotion/video_resources/channels/sleep_travel/assets/bgm/`
- エフェクトテンプレート: `Remotion/video_resources/channels/sleep_travel/effects/templates/`

## 素材選択ルール（必須）
- 素材選択時は、対象フォルダを走査して「実在する候補ファイル」を番号付きで提示する。
- 「音声素材 / 台本 / 背景画像 / BGM / エフェクト設定」の5項目を1つずつ順番に確定する。
- 拡張子フィルタ:
- 音声素材: `.wav` `.mp3`
- 台本: `.md` `.txt`
- 背景画像: `.png` `.jpg` `.jpeg`
- BGM: `.wav` `.mp3`
- 候補0件の項目があれば、先に不足を報告して補充を依頼する。
- カスタムエフェクトを新規作成した場合は、都度「日本語名」を付けてテンプレートとして保存する。
- エフェクトテンプレート保存先: `Remotion/video_resources/channels/sleep_travel/effects/templates/`
- 保存時は、次回再利用できるよう目的・適用シーン・主要パラメータを残す。

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
- BGMをシームレスループ
- 字幕を音声進行に合わせる
- 字幕をフェードイン/フェードアウト
- 白線のシンプルなオーディオスペクトラム表示
6. 必要なら `Remotion/my-video/src/Root.tsx` にCompositionを追加する。
7. `Remotion/my-video/` で `npm run lint` を実行する。
8. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `npx remotion render ...` コマンドを提示する。
- レンダリング前の確認文言は必ず `出力しますか？書き出しますか？` を使う。
- 過去ターンで承認があっても、レンダリング直前に毎回確認する。
9. 実施内容、編集ファイル、lint結果を報告する。
