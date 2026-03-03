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
- `Remotion/my-video/public/assets/channels/acoriel/channel_info.md`
- `Remotion/my-video/public/assets/channels/acoriel/templates/acoustic_cover_multifont_fade_subtitle.md`
- `Remotion/my-video/src/AcoRielCover.tsx`
- `Remotion/my-video/src/AcoRielLyricCover.tsx`
- `Remotion/my-video/src/Root.tsx`

## プロジェクト構成（曲ごと分離・必須）

曲ごとに独立したプロジェクトとして管理する。既存の曲フォルダは削除しない。

```
Remotion/my-video/
├── src/
│   ├── AcoRielCover.tsx          # 共通テンプレート（props受け取り）
│   ├── AcoRielLyricCover.tsx     # 共通テンプレート（LyricCover / MultiBG 両方含む）
│   ├── Root.tsx                  # 全曲のCompositionを登録（曲ごとに追記）
│   └── index.ts
└── public/
    └── assets/
        ├── songs/
        │   ├── [曲名]/                  # 曲ごとのサブフォルダ
        │   │   ├── audio.mp3            # 音源（WAV→MP3変換済み）
        │   │   ├── background.png       # 背景画像（LyricCoverテンプレ時）
        │   │   ├── bg_video_1.mp4       # 背景動画（MultiBGテンプレ時）※ユーザーが配置
        │   │   ├── bg_video_2.mp4       #   〃
        │   │   ├── bg_video_3.mp4       #   〃（本数は任意）
        │   │   └── lyric_animation_data.json  # 歌詞アニメーションデータ
        │   └── ...
        └── [共通アセット]        # channel-icon.png / fonts/ など
```

### 曲フォルダ命名規則
- `Remotion/my-video/public/assets/songs/[曲名]/`
- **スペースはアンダースコアに変換する**（例: `LOVE_PHANTOM`、`Tomorrow_never_knows`）
- `staticFile()` はスペース入りパスを正しく解決できないため、フォルダ名にスペースを含めない。

### Root.tsx への登録ルール
- 新曲追加時は既存のCompositionを消さず、末尾に追記する
- **Composition ID に使えるのは `a-z A-Z 0-9 漢字（Han）-` のみ**。アンダースコア `_`、ひらがな、カタカナは使用禁止。
  - OK例: `AcoRiel-LOVE-PHANTOM`、`AcoRiel-TomorrowNeverKnows-Lyric`、`AcoRiel-Seishun-Amigo-MultiBG`
  - NG例: `AcoRiel_LOVE_PHANTOM`（アンダースコア）、`AcoRiel-拝啓十五の君へ-MultiBG`（ひらがな「へ」を含む）
  - 日本語曲名はローマ字表記にする（例: 青春アミーゴ→`Seishun-Amigo`、手紙→`Tegami`）
- 削除はユーザーが明示的に指示した場合のみ行う

### MultiBG の曲フォルダ構成（事前合成動画使用時）

```
songs/[曲名]/
├── audio.mp3
├── lyric_animation_data.json
├── bg_prerendered.mp4        ← prerender_bg_video.py で生成する（必須）
└── freepik_*.mp4 など         ← 素材動画（prerender後はRemotionから参照しない）
```

## 素材参照先
- カバー曲音源: `Remotion/my-video/public/assets/channels/acoriel/songs/`
- 歌詞TXT: `Remotion/my-video/public/assets/channels/acoriel/lyrics/`
- 歌詞LRC（既存/生成先）: `Remotion/scripts/lyrics/`
- 背景画像: `Remotion/my-video/public/assets/channels/acoriel/backgrounds/`
- エフェクトテンプレート: `Remotion/my-video/public/assets/channels/acoriel/effects/templates/`

## 音源フォーマットルール（必須）

Remotion レンダリング中のメモリ枯渇・タイムアウトを防ぐため、**音源は必ず MP3 で管理する**。未圧縮 WAV（40〜55MB 程度）を使うと `getAudioData()` がメモリを大量消費し、数千フレーム後にブラウザがフリーズする。

### 変換コマンド（ffmpeg）

```bash
ffmpeg -i "<入力ファイル>.wav" -q:a 2 "<出力ファイル>.mp3"
```

- `-q:a 2`: VBR 品質 2（約190kbps）。音楽カバーに十分な高品質。
- 出力先は `Remotion/my-video/public/assets/channels/acoriel/songs/`
- コード側（`AcoRielCover.tsx` / `AcoRielLyricCover.tsx`）は MP3 を直接参照する。

### 変換後の確認

```bash
ls -lh Remotion/my-video/public/assets/channels/acoriel/songs/<曲名>.mp3  # 5MB前後になっていること
```

## テンプレート選択ルール（必須）

編集テンプレートを先に確定してから素材選択を行う。

| テンプレート | コンポーネント | 背景素材 |
|---|---|---|
| `LyricCover`（標準） | `AcoRielLyricCover` | 静止画 1枚（`background.png`）|
| `MultiBG`（動画背景） | `AcoRielLyricCoverMultiBG` | 動画複数本（`bg_video_*.mp4`）|

## 素材選択ルール（必須）
- 素材選択時は対象フォルダを走査し、実在する候補のみ番号付きで提示する。
- 前回選択の自動流用は禁止し、背景素材とエフェクトは毎回選び直す。
- 以下を1項目ずつ順番に確定する:
1. カバー曲音源（`.mp3`）
2. 歌詞TXT（`.txt`）— **任意**。歌詞字幕を使わない場合はスキップ可能。
3. **背景素材**（テンプレートによって異なる）
   - `LyricCover` の場合: 背景画像（`.png` `.jpg` `.jpeg`）を選択する
   - `MultiBG` の場合:
     1. 曲フォルダ `Remotion/my-video/public/assets/songs/[曲名]/` を即座に作成する。
     2. ユーザーに以下を表示して待機する:
        ```
        背景動画ファイルを以下のフォルダに配置してください。
        配置先: Remotion/my-video/public/assets/songs/[曲名]/
        ファイル名は自由（例: bg_video_1.mp4, 夏の海.mp4 など）
        配置が完了したら「準備できました」と教えてください。
        ```
     3. ユーザーから配置完了の応答が得られたら、フォルダを `ls` でスキャンし実在する `.mp4` ファイル一覧を取得する。
     4. 取得したファイル名をそのまま `backgroundVideos` props に使用する。
4. エフェクト設定（既存テンプレート or 新規作成）
- 候補0件の**必須**項目（曲・背景）があれば編集を止め、不足素材を報告する。
- カスタムエフェクトを新規作成した場合は、都度日本語名を付けて保存する。
- 保存先: `Remotion/my-video/public/assets/channels/acoriel/effects/templates/`

### LRC解決ルール（必須）
- 歌詞TXTを選択した場合は、以下の順で `lyrics.lrc` を確定する:
1. `Remotion/scripts/lyrics/` に該当曲のLRCがあればそれを採用する。
2. 該当LRCが無ければ、**字幕生成スクリプト** で作成する。以下のコマンドをユーザーに提示し、**プロジェクトルート（`team-info/`）から別ターミナルで実行**するよう案内して待機する:
   ```bash
   Remotion/.venv/bin/python3.11 -u .agent/skills/remotion/lyric-emotion-mapper/scripts/transcribe_to_lrc.py "Remotion/my-video/public/assets/channels/acoriel/songs/[曲名].mp3" --lyrics "Remotion/my-video/public/assets/channels/acoriel/lyrics/[曲名].txt" --output "Remotion/scripts/lyrics/[曲名].lrc" --output-format lrc --intro-label "(イントロ)" --intro-min-seconds 0.30 --model large-v3 --language ja
   ```
   - このコマンドは先頭イントロ `(イントロ)` を自動挿入し、最初の歌詞開始時刻を単語単位で合わせる。
   - `-u` と進捗バーで長時間処理中の進捗が見える。
   - コマンドは常にプロジェクトルートからの相対パスで提示する（`cd` 不要の1行コマンド）。
   - 完了したら「終わりました」と伝えるよう案内する。
   - ユーザーから完了報告が得られるまで次工程に進まない。
   - 完了後、`Remotion/scripts/lyrics/` をスキャンし、生成された `.lrc` ファイルを確認する。
- LRC確定後は、**必ず**歌詞TXTと行単位で照合し、誤字脱字・欠落・不要行がないことを確認する。
- 照合で問題があればLRCを修正し、問題が解消するまで次工程に進まない。

### LRCへの間奏・アウトロ挿入ルール（必須）

LRC照合が完了したら、以下のルールで間奏・アウトロを挿入または確認する:

**間奏（instrumental）の挿入**
- 連続する2行のLRCエントリを比べたとき、前の行のタイムスタンプから **8秒以上** 後に次の行が来る場合、その空白期間を「間奏」とみなす。
- 間奏の開始タイムスタンプを決める:
  - 前の行の歌詞が歌い終わる頃（前の行のタイムスタンプ + 推定歌唱時間、目安は5〜8秒）に `（間奏）` エントリを挿入する。
  - 不明な場合は前の行タイムスタンプ + 5秒を目安にする。
- 挿入フォーマット例:
  ```
  [01:50.94]抱きしめて
  [01:55.94]（間奏）          ← 前行の5秒後
  [02:12.98]辿り着いた
  ```

**アウトロの挿入**
- 最後の歌詞行のあと、音源終了まで **5秒以上** 残っている場合、アウトロとみなす。
- 最後の歌詞が歌い終わる頃（最後の行タイムスタンプ + 推定歌唱時間）に `（アウトロ）` エントリを挿入する。
- 挿入フォーマット例:
  ```
  [04:53.09]抱きしめて
  [04:57.09]（アウトロ）      ← 最後の歌詞の4秒後、音源終了まで続く
  ```

**LRCを変更したらJSONにも反映させる（必須）**
- LRCを変更した場合、`lyric_animation_data.json` も必ず更新する。
- 間奏・アウトロエントリをJSONに追加し、直前のエントリの `duration` を短縮して間奏開始時刻に合わせる。

### AIカバー時の追加ルール（必須）
- AIカバーの場合は、以下を毎回この順で確定する:
1. アカウント情報
2. 編集テンプレ
3. 音源
4. 背景画像
5. エフェクト
6. 歌詞TXT（カラオケ版を作る場合のみ）
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

## 事前確認フロー（Phase 0）

スキル起動直後、編集を始める前に以下を順番に実施する。

### Step 0-1: 全体フローを提示

ユーザーに以下の全体フローを表示する：

```
【制作フロー】
Phase 0: 事前確認（← いまここ）
  └ フロー提示 → 素材置き場案内 → 素材チェック → 準備確認

Phase 1: テンプレート＆素材選択
  └ テンプレート選択 → 音源/歌詞/背景/エフェクト確定

Phase 2: LRC・概要欄生成
  └ LRC確定（Whisper or 既存）→ 歌詞照合 → 概要欄生成

Phase 3: Remotion実装
  └ 曲フォルダ作成 → JSON生成 → （MultiBG: 背景動画事前合成） → Root.tsx追記

Phase 4: 確認・レンダリング
  └ lint → remotion studio → レンダリング（承認後）
```

### Step 0-2: 素材の置き場所を案内

以下の表をユーザーに提示する：

| 素材の種類 | 置き場所 | ファイル形式 |
|---|---|---|
| 音源 | `Remotion/my-video/public/assets/channels/acoriel/songs/` | `.mp3`（WAV不可） |
| 歌詞TXT | `Remotion/my-video/public/assets/channels/acoriel/lyrics/` | `.txt` |
| 背景画像 | `Remotion/my-video/public/assets/channels/acoriel/backgrounds/` | `.png` `.jpg` `.jpeg` |
| 歌詞LRC（既存） | `Remotion/scripts/lyrics/` | `.lrc` |
| エフェクトテンプレ | `Remotion/my-video/public/assets/channels/acoriel/effects/templates/` | `.md` |
| 背景動画（MultiBG用） | 後で `Remotion/my-video/public/assets/songs/[曲名]/` に配置 | `.mp4` |

### Step 0-3: 素材チェック（フォルダスキャン）

以下の5つのフォルダを `ls` でスキャンし、現在の素材をユーザーに提示する：

- `Remotion/my-video/public/assets/channels/acoriel/songs/`
- `Remotion/my-video/public/assets/channels/acoriel/lyrics/`
- `Remotion/my-video/public/assets/channels/acoriel/backgrounds/`
- `Remotion/scripts/lyrics/`
- `Remotion/my-video/public/assets/channels/acoriel/effects/templates/`

提示フォーマット例：
```
【現在の素材状況】
🎵 音源（songs/）: SAY_YES.mp3, LOVE_PHANTOM.mp3 ... （N件）
📝 歌詞TXT（lyrics/）: SAY YES.txt ... （N件）
🖼️ 背景画像（backgrounds/）: ギター窓.png ... （N件）
🎬 LRC（scripts/lyrics/）: SAY_YES_Chage_and_Aska.lrc ... （N件）
✨ エフェクト（effects/templates/）: 銀粒子_低刺激リリック.md ... （N件）

⚠️ 音源がまだない場合は上記フォルダに MP3 を追加してください。
```

### Step 0-4: 準備確認（必須ゲート）

以下のメッセージをユーザーに表示し、確認応答を待つ：

```
制作を始める曲の素材は揃っていますか？
最低限必要なもの：
  ✅ 音源（.mp3）
  ✅ 背景画像（.png/.jpg）— LyricCover の場合

揃っていれば「準備できました」と教えてください。
追加素材がある場合は素材を配置してから教えてください。
```

- ユーザーの確認応答を受けて初めて以下の `## 編集フロー` の Step 1 に進む。
- 確認前に Step 1 以降を実行してはならない。

---

## 編集フロー
1. チャンネル情報とテンプレート仕様を読み、トーン（エレガント・透明感）を固定する。
1.5. **編集テンプレートを選択する**（必須）
   - `LyricCover`（標準・静止画背景）か `MultiBG`（動画背景クロスディゾルブ）かを確定する。
   - 選択後、以降のフローが対応するテンプレートの手順に分岐する。
2. 素材4項目を順番に確定する。
2.5. **概要欄を生成する**（スキル: `acoriel-video-description`）
   - 曲名・原曲アーティスト名が確定した時点で実行する。
   - ユーザーから一言メモがあれば反映、なければ曲名から連想して生成。
3. **歌詞LRCを確定する**（歌詞字幕を使う場合・必須）
   - 選択済みTXTに対応するLRCを `Remotion/scripts/lyrics/` から探索する。
   - 見つからなければ `transcribe_to_lrc.py` で音源からLRCを生成する。
   - 生成/採用したLRCを、歌詞TXTと照合して誤字脱字・欠落がないことを確認する。
4. **曲フォルダを作成する**（必須）
   - フォルダ名のスペースはアンダースコアに変換する（例: `Tomorrow_never_knows`）
   - `Remotion/my-video/public/assets/songs/[曲名_スペースなし]/` を新規作成する。
   - 音源は **WAV → MP3 変換してから** `audio.mp3` として配置する（上記「音源変換ルール」参照）。
   - `LyricCover` の場合: 背景画像・歌詞LRCをそのままコピーする。
   - `MultiBG` の場合: 歌詞LRCのみコピーする。背景動画はユーザーが手動配置するため、この時点では配置しない。
4.3. **（MultiBG のみ）背景動画を事前合成する**（必須）
   - まず音源の実尺を取得する（これを `--total-sec` に使う）:
     ```bash
     ffprobe -v quiet -print_format json -show_format \
       Remotion/my-video/public/assets/songs/[曲名]/audio.mp3 \
       | python3 -c "import sys,json; d=json.load(sys.stdin); print(round(float(d['format']['duration']), 3))"
     ```
   - 取得した秒数を確認したら、**自分では実行せず**、以下のコマンドをユーザーに提示して**プロジェクトルート（`team-info/`）から別ターミナルで実行**するよう案内して待機する:
     ```bash
     python3 Remotion/scripts/prerender_bg_video.py \
       --output Remotion/my-video/public/assets/songs/[曲名]/bg_prerendered.mp4 \
       --crossfade-sec 1.5 \
       --total-sec [音源の秒数] \
       --fps 30 --width 1920 --height 1080 \
       --ping-pong \
       "Remotion/my-video/public/assets/songs/[曲名]/"*.mp4
     ```
   - 完了したら「終わりました」と伝えるよう案内する。
   - ユーザーから完了報告が得られるまで次工程に進まない。
   - `--ping-pong`: 各クリップを順再生→逆再生（計 min_dur×2 秒）で繋ぐ。ループ感が出ず、2往復で自然に次の素材へ切り替わる。`--segment-sec` は自動計算されるので不要。
   - `--crossfade-sec 1.5`: クリップ切り替え時に1.5秒フェード。
   - 既存の `bg_prerendered_seed*.mp4` は入力グロブから自動除外される。
   - `--total-sec` は必ず音源の実尺（ffprobeで取得）を使う。`durationInFrames ÷ fps` は誤差が出る場合があるので使わない。
   - 出力ファイル名は seed 値込みで自動決定される（例: `bg_prerendered_seed1872634591.mp4`）。
   - 完了ログに以下が表示されるのでファイル名を控える:
     ```
     ▶ Root.tsx に設定するファイル名: 'bg_prerendered_seed1872634591.mp4'
        prerenderedBgVideo: 'bg_prerendered_seed1872634591.mp4'
     ```
   - 完了後、Root.tsx の該当 Composition の `prerenderedBgVideo` をログのファイル名に更新する。
   - 既存の曲フォルダは触らない。
4.25. **（削除）** 背景動画の配置確認は 素材選択ルール の `MultiBG` 手順（素材 3/4）に統合済み。このステップはスキップする。
4.5. **`lyric_animation_data.json` を新規作成する**（歌詞字幕を使う場合・必須）
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
   - **間奏・アウトロエントリの扱い:**
     - LRCに `（間奏）` があれば JSON にもそのままエントリを追加する。直前エントリの `duration` は `（間奏）` の開始時刻 - 直前エントリの `time` に短縮する。
     - LRCに `（アウトロ）` があれば JSON に追加する。直前エントリの `duration` を短縮し、アウトロエントリの `duration` は `音源終了秒 - アウトロ開始時刻` にする。
     - 間奏・アウトロエントリは `"label": "Verse"` で、`animation.in` は `"Karaoke"`、`inDurationFrames: 15, outDurationFrames: 15` を使う。
     - `words` は `[{"word": "（間奏）", "start": 0, "end": min(duration, 3.0)}]` のように1フレーズで収める。
   - 最終エントリ（アウトロがある場合はアウトロ）の `duration` は `音源終了秒 - time` で埋める。
   - 作成後 `Remotion/my-video/public/assets/songs/[曲名]/lyric_animation_data.json` に保存する。
5. `AcoRielLyricCover.tsx` が props（`songFolder` など）でアセットパスを切り替えられる構造になっているか確認し、必要なら対応する。
6. `Root.tsx` に今回の曲のCompositionを**追記**する（既存Compositionは削除しない）。
   - Composition ID は **ハイフン区切り**で命名する（アンダースコア禁止）
   - `LyricCover` の場合: `AcoRiel-[曲名]-Lyric`（例: `AcoRiel-TomorrowNeverKnows-Lyric`）
   - `MultiBG` の場合: `AcoRiel-[曲名]-MultiBG`（例: `AcoRiel-SAY-YES-MultiBG`）
   - `MultiBG` の場合は、Step 4.3 の完了ログに表示された `prerenderedBgVideo: 'bg_prerendered_seed[N].mp4'` の値を props に設定する（`backgroundVideos` などは不要）。
   - 対応する曲フォルダのパスをpropsで渡す。
7. `Remotion/my-video/` で `npm run lint` を実行し、エラーを解消する。
8. lint 通過後、以下のコマンドをユーザーに提示してプレビューを依頼する（自分では起動しない）：
   ```bash
   cd Remotion/my-video && npx remotion studio
   ```
   - `Remotion/my-video/` ディレクトリから実行してください、と案内する。
   - サイドバーで対象 Composition を選んで確認するよう伝える。
   - プレビュー確認後、問題があれば報告するよう伝える。
9. レンダリングは実行しない。以下のコピペ可能なコマンドをユーザーに提示するだけにする：
   ```bash
   cd Remotion/my-video && npx remotion render --composition=AcoRiel-[曲名]-MultiBG --output=../../outputs/acoriel/renders/[曲名].mp4
   ```
   - 出力先: `outputs/acoriel/renders/[曲名].mp4`
10. 実施内容、編集ファイル、lint結果、ローカル確認方法、残タスク（素材差し替えなど）を報告する。
