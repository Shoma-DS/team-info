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
- `Remotion/my-video/src/AcoRielLyricCover.tsx`
- `Remotion/my-video/src/Root.tsx`

## 素材参照先
- カバー曲音源: `Remotion/video_resources/channels/acoriel/assets/songs/`
- 歌詞（LRC）: `Remotion/scripts/lyrics/`
- 背景画像: `Remotion/video_resources/channels/acoriel/assets/backgrounds/`
- エフェクトテンプレート: `Remotion/video_resources/channels/acoriel/effects/templates/`

## 素材選択ルール（必須）
- 素材選択時は対象フォルダを走査し、実在する候補のみ番号付きで提示する。
- 前回選択の自動流用は禁止し、背景画像とエフェクトは毎回選び直す。
- 以下を1項目ずつ順番に確定する:
1. カバー曲音源（`.wav` `.mp3`）
2. 歌詞LRC（`.lrc`）— **任意**。歌詞字幕は後で手動編集するため、スキップ可能。
3. 背景画像（`.png` `.jpg` `.jpeg`）
4. エフェクト設定（既存テンプレート or 新規作成）
- 候補0件の**必須**項目（曲・背景）があれば編集を止め、不足素材を報告する。
- カスタムエフェクトを新規作成した場合は、都度日本語名を付けて保存する。
- 保存先: `Remotion/video_resources/channels/acoriel/effects/templates/`

### AIカバー時の追加ルール（必須）
- AIカバーの場合は、以下を毎回この順で確定する:
1. アカウント情報
2. 編集テンプレ
3. 音源
4. 背景画像
5. エフェクト
6. 歌詞ファイル（カラオケ版を作る場合のみ）

## フォントルール（固定）
- 今後の `acoriel/acoustic_cover` では以下をデフォルトにする:
1. 漢字: `Hachi Maru Pop`
2. 英字・数字: `Playwrite NZ Basic`（Google Fonts CSS読み込みで可）
3. ひらがな: `Yosugara`
4. カタカナ: `Yosugara`
- 実装時は文字種ごとに `span` を分けて `fontFamily` を切り替える。
- 単一 `fontFamily` 指定で全字幕を描画しない。
- イントロ/アウトロ/歌詞字幕すべて同じルールで適用する。

### フォント実装メモ
- `AcoRielCover.tsx` / `AcoRielLyricCover.tsx` の両方に、文字種判定ヘルパーを置く。
- 文字種判定の基準:
  - `Hiragana` -> ひらがな扱い
  - `Katakana` -> ひらがな扱い（Yosugaraへ）
  - `Han` -> 漢字扱い
  - `[A-Za-z0-9]` -> 英字扱い
- `Playwrite NZ Basic` が `@remotion/google-fonts` に無い場合は、`<link rel="stylesheet">` で読み込んで使う。
- 既存コードでフォントを差し替える際、`npm run lint` を必ず通す。

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
7. `Remotion/my-video/` で `npx remotion studio` を起動し、対象Compositionをローカル確認できる状態にする。
8. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `npx remotion render ...` コマンドを提示する。
9. 実施内容、編集ファイル、lint結果、ローカル確認方法、残タスク（素材差し替えなど）を報告する。
