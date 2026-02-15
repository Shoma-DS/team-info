---
name: remotion-template-acoriel-acoustic-cover
description: acorielチャンネルのacoustic_coverテンプレート専用編集スキル。懐メロ中心のアコースティックカバー向けリリックビデオをRemotionで制作する。
---

# acoriel acoustic_cover 専用スキル

## 入力前提
- チャンネル: `acoriel`
- テンプレート: `acoustic_cover`
- 親スキル `remotion-video-production` で選択済みであること。

## 参照ファイル
- `Remotion/video_resources/channels/acoriel/channel_info.md`
- `Remotion/video_resources/channels/acoriel/templates/acoustic_cover.md`
- `Remotion/my-video/src/AcoRielCover.tsx`
- `Remotion/my-video/src/Root.tsx`

## 素材参照先
- カバー曲音源: `Remotion/video_resources/channels/acoriel/assets/songs/`
- 歌詞（LRC）: `Remotion/scripts/lyrics/`
- 背景画像: `Remotion/video_resources/channels/acoriel/assets/backgrounds/`
- エフェクトテンプレート: `Remotion/video_resources/channels/acoriel/effects/templates/`

## 素材選択ルール（必須）
- 素材選択時は対象フォルダを走査し、実在する候補のみ番号付きで提示する。
- 以下を1項目ずつ順番に確定する:
1. カバー曲音源（`.wav` `.mp3`）
2. 歌詞LRC（`.lrc`）— **任意**。歌詞字幕は後で手動編集するため、スキップ可能。
3. 背景画像（`.png` `.jpg` `.jpeg`）
4. エフェクト設定（既存テンプレート or 新規作成）
- 候補0件の**必須**項目（曲・背景）があれば編集を止め、不足素材を報告する。
- カスタムエフェクトを新規作成した場合は、都度日本語名を付けて保存する。
- 保存先: `Remotion/video_resources/channels/acoriel/effects/templates/`

## 編集フロー
1. チャンネル情報とテンプレート仕様を読み、トーン（エレガント・透明感）を固定する。
2. 素材4項目を順番に確定する。
3. `AcoRielCover.tsx` を更新し、以下を満たす:
- イントロ（曲名 / Original by / Covered by）
- メイン（背景 + パーティクル + スペクトラム）
- アウトロ（AcoRiel表示 + 登録案内）
- 歌詞字幕は後で手動編集するため、コード側では実装しない
4. 必要なら `Root.tsx` に `AcoRielCover` の Composition を追加/更新する。
5. `Remotion/my-video/public/assets/` の参照ファイル名整合を確認する。
6. `Remotion/my-video/` で `npm run lint` を実行し、エラーを解消する。
7. 実施内容、編集ファイル、lint結果、残タスク（素材差し替えなど）を報告する。
