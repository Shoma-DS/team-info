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

## プロジェクト構成（曲ごと分離・必須）

曲ごとに独立したプロジェクトとして管理する。既存の曲フォルダは削除しない。

```
Remotion/my-video/
├── src/
│   ├── AcoRielCover.tsx          # 共通テンプレート（props受け取り）
│   ├── AcoRielLyricCover.tsx     # 共通テンプレート
│   ├── Root.tsx                  # 全曲のCompositionを登録（曲ごとに追記）
│   └── index.ts
└── public/
    └── assets/
        ├── songs/
        │   ├── [曲名]/           # 曲ごとのサブフォルダ
        │   │   ├── audio.wav     # 音源
        │   │   ├── background.png # 背景画像
        │   │   └── lyrics.lrc   # 歌詞（任意）
        │   └── ...
        └── [共通アセット]        # channel-icon.png / fonts/ など
```

### 曲フォルダ命名規則
- `Remotion/my-video/public/assets/songs/[曲名]/`
- **スペースはアンダースコアに変換する**（例: `LOVE_PHANTOM`、`Tomorrow_never_knows`）
- `staticFile()` はスペース入りパスを正しく解決できないため、フォルダ名にスペースを含めない。

### Root.tsx への登録ルール
- 新曲追加時は既存のCompositionを消さず、末尾に追記する
- **Composition ID に使えるのは `a-z A-Z 0-9 CJK文字 -` のみ**。アンダースコア `_` は使用禁止。
  - OK例: `AcoRiel-LOVE-PHANTOM`、`AcoRiel-TomorrowNeverKnows-Lyric`
  - NG例: `AcoRiel_LOVE_PHANTOM`（Remotionがエラーを投げて全Compositionが壊れる）
- 削除はユーザーが明示的に指示した場合のみ行う

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
7. **概要欄を生成する**（スキル: `acoriel-video-description`）
   - 音源（曲名・アーティスト）が確定した時点（ステップ3の直後）で実行してよい。
   - 一言メモがあれば反映、なければ曲名から連想して生成。

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
2.5. **概要欄を生成する**（スキル: `acoriel-video-description`）
   - 曲名・原曲アーティスト名が確定した時点で実行する。
   - ユーザーから一言メモがあれば反映、なければ曲名から連想して生成。
3. **曲フォルダを作成する**（必須）
   - フォルダ名のスペースはアンダースコアに変換する（例: `Tomorrow_never_knows`）
   - `Remotion/my-video/public/assets/songs/[曲名_スペースなし]/` を新規作成する。
   - 音源・背景画像・歌詞LRCをこのフォルダにコピーする。
   - 既存の曲フォルダは触らない。
3.5. **`lyric_animation_data.json` を新規作成する**（歌詞字幕を使う場合・必須）
   - **絶対に他の曲の `lyric_animation_data.json` をコピーして流用しない**（歌詞が別曲になる）。
   - LRC ファイルのタイムスタンプを秒に変換し、以下のフォーマットで JSON を生成する:
     ```json
     [
       {
         "time": <音源開始からの秒数>,
         "duration": <次のエントリとの差分秒数>,
         "text": "<歌詞テキスト>",
         "label": "Verse" または "サビ" または "Bridge",
         "emotion": "",
         "words": [
           { "word": "<フレーズ>", "start": <エントリ内相対秒>, "end": <エントリ内相対秒> }
         ],
         "animation": { "in": "Karaoke", "out": "FadeOut", "props": { "inDurationFrames": 10, "outDurationFrames": 8 } }
       }
     ]
     ```
   - `words` の `start`/`end` はそのエントリの `time` からの相対秒数（0始まり）。
   - サビ行は `"label": "サビ"` にするとフォントサイズ・グロウが強調される。
   - 最終エントリの `duration` は全体尺 - `time` で埋める。
   - 作成後 `Remotion/my-video/public/assets/songs/[曲名]/lyric_animation_data.json` に保存する。
4. `AcoRielLyricCover.tsx` が props（`songFolder` など）でアセットパスを切り替えられる構造になっているか確認し、必要なら対応する。
5. `Root.tsx` に今回の曲のCompositionを**追記**する（既存Compositionは削除しない）。
   - Composition ID は **ハイフン区切り**で命名する（アンダースコア禁止）
   - OK例: `AcoRiel-LOVE-PHANTOM`、`AcoRiel-TomorrowNeverKnows-Lyric`
   - 対応する曲フォルダのパスをpropsで渡す。
6. `Remotion/my-video/` で `npm run lint` を実行し、エラーを解消する。
7. **`Remotion/my-video/` ディレクトリから** `npx remotion studio` を起動する。
   - 起動コマンド例: `cd /path/to/Remotion/my-video && npx remotion studio`
   - **誤ったディレクトリから起動するとプロジェクトが認識されず黒画面になる。**
8. レンダリングは勝手に実行しない。必要な場合はユーザー承認を取るか、コピペ可能な `npx remotion render ...` コマンドを提示する。
   - レンダリング出力先: `Remotion/renders/[曲名].mp4`
9. 実施内容、編集ファイル、lint結果、ローカル確認方法、残タスク（素材差し替えなど）を報告する。
