---
name: lyric-video-production
description: 音声と歌詞からLRC生成、感情分析、Remotionリリックアニメーション実装までを一貫して行うリリックビデオ制作ワークフロー。
---

# Lyric Video Production Workflow

音声ファイルと歌詞テキストから、Remotionで実装可能なリリックアニメーションビデオを制作するための3フェーズワークフロー。

## 絶対パスルール（必須）
- ユーザーにコマンドを渡すときは、固定の `/Users/...` ではなく `TEAM_INFO_ROOT` から絶対パスを組み立てる。
- `cd Remotion/...` や `python .agent/...` のような相対パスのコマンドは渡さない。

## 役割
あなたは「Remotionエンジニア」兼「リリックビデオ演出家」です。
Whisperによる音声認識、感情分析、Remotionコード生成までを一貫して行います。

---

## 標準オペレーション（必須）

今後このスキルを使うときは、必ず以下の順で進行する。

1. アカウント選択
2. 編集テンプレ選択
3. 素材選択
4. Remotion 反映

### 編集テンプレ

- `Karaoke Style`:
  単語タイムスタンプ同期のカラオケ字幕。今回の実装（カラオケ進行、2行分割、字幕グロー、クロスディゾルブ）を標準とする。
- `Lyric Animation Style`:
  感情別の入退場アニメーションを中心にしたリリック演出。

### Karaoke Style の固定仕様（編集テンプレ標準）

`Karaoke Style` を選んだ場合は、以下を毎回適用する。

1. 歌詞字幕はタイトルと同じフォント系（手書きトーン）を使う
2. 歌詞字幕には常時グローを入れる
3. テキスト出現はクロスディゾルブで行う
4. 長い歌詞は意味の塊を優先して2行分割する
5. 歌詞字幕レイヤーは `Sequence` 1本で運用する（行ごとSequence禁止）
6. タイトル出現は筆順風（ストローク→塗り）を優先する
7. 音源終端は約0.5秒でフェードアウトさせる
8. CTA（チャンネル登録）は「音源終了約0.3秒前」から表示し、末尾に約2秒の無音余韻を確保する
9. CTAと歌詞字幕は重ねない
10. 背景画像は毎回候補一覧から選択する（前回設定の自動流用は禁止）
11. エフェクト設定は毎回候補一覧から選択する（前回設定の自動流用は禁止）

### AIカバー運用ルール（必須）

`AIカバー` として制作する場合、Phase 0 では以下を毎回この順で選択する。

1. アカウント情報
2. 編集テンプレ（`Karaoke Style` / `Lyric Animation Style`）
3. 音源
4. 背景画像
5. エフェクト
6. 歌詞ファイル（**Karaoke Style のときだけ必須**）

補足:
- `Lyric Animation Style` では歌詞ファイル選択は必須にしない（必要時のみ選択）。
- 背景画像・音源・エフェクトは毎回ユーザー選択で確定する。

### 歌詞字幕レイヤー実装ルール（全アカウント共通・必須）

アカウント種別に関わらず、歌詞字幕は必ず以下で実装する。

1. `Sequence` は歌詞レイヤー全体で **1本のみ**
2. 行ごとに `data.map(...<Sequence>...)` を作らない
3. 現在フレームから「アクティブな1行」を選択して描画する
4. 行内アニメーションは `lineFrame`（行相対フレーム）で計算する
5. 歌詞字幕レイヤーを含め、生成・更新する **すべての `<Sequence>` に `name` を付ける**（例: `歌詞字幕`, `背景画像`, `補助字幕`, `音声`）

目的:
- タイムラインを見やすく保つ
- 編集時の操作負荷を下げる
- 長尺曲での管理コストを下げる

### メディアレイヤー統合ルール（全アカウント共通・必須）

- 画像、動画、音声、字幕など、同じ種類で時系列が重ならない素材は、その種類ごとに `<Sequence>` を1本へ統合する。
- `map(...<Sequence>...)` で非重複な同種素材を量産せず、現在フレームからアクティブな素材を選択して描画・再生する。
- 複数 `<Sequence>` を許可するのは、同種素材の同時表示/同時再生、独立レイヤー合成、クロスフェードなど、時間重複が必要な場合のみとする。
- 歌詞字幕レイヤーはこの原則の最優先適用対象とし、既存実装が複数Sequence方式なら1本化してから編集を進める。
- 各 `<Sequence>` の `name` は必須。Studio のタイムラインで役割が分かる日本語名を付ける。

### Whisper 実行確認（必須）

テンプレが `Karaoke Style` または `Lyric Animation Style` の場合、Phase 1を実行する前に必ずユーザーへ確認する。

- 「Whisper音声認識（LRC + lyric_animation_data.json再生成）を今回実行しますか？」
- `Yes`: Phase 1を実行して再生成する
- `No`: 既存の `lyrics.lrc` / `lyric_animation_data.json` をそのまま使ってPhase 2へ進む

### イントロ/アウトロの補助字幕（必須確認）

実歌唱と歌詞テキストに差がある場合（前奏・後奏・アレンジ区間）は、ユーザーに確認して補助字幕を入れる。

- 例: `(イントロ)`, `(アウトロ)`
- 補助字幕も `Karaoke` で追えるように `lyric_animation_data.json` の `words` を設定する
- 補助字幕を入れたら LRC と JSON の両方を同時更新する

---

## Phase 0: アカウント選択・テンプレ選択・素材選択（インタラクティブ）

**このフェーズでは、ユーザーに対話的に進行条件を確定させる。**

### 0-0. アカウント選択

どのチャンネル/アカウント向けに制作するかを先に確定する。

例:
- `acoriel`
- その他ユーザー指定のアカウント

アカウントに応じて `Remotion/my-video/public/assets/channels/<account>/` を参照する。

### 0-1. 編集テンプレ選択

以下から選択させる:
- `Karaoke Style`
- `Lyric Animation Style`

テンプレ選択後、上記の Whisper 実行確認を必ず行う。

### 0-2. 音源の選択

音源ディレクトリを一覧表示し、ユーザーに選択させる。

```
音源ディレクトリ: Remotion/my-video/public/assets/channels/acoriel/songs/
```

**手順:**
1. `ls` でディレクトリ内のファイルを一覧表示する
2. ユーザーに「どの曲を使いますか？」と AskUserQuestion で質問する
3. 選択された音源ファイルのパスを記録する

### 0-3. 背景画像の選択（毎回必須）

背景画像ディレクトリを一覧表示し、ユーザーに選択させる。

```
背景画像ディレクトリ: Remotion/my-video/public/assets/channels/<account>/backgrounds/
```

**手順:**
1. `ls` でディレクトリ内の画像ファイル（`.png` `.jpg` `.jpeg`）を一覧表示する
2. ユーザーに「どの背景画像を使いますか？」と質問する
3. 選択された背景画像ファイルのパスを記録する

### 0-4. エフェクトの選択（毎回必須）

エフェクトテンプレートを一覧表示し、ユーザーに選択させる。

```
エフェクトテンプレート: Remotion/my-video/public/assets/channels/<account>/effects/templates/
```

**手順:**
1. `ls` でテンプレートファイルを一覧表示する
2. ユーザーに「どのエフェクトを使いますか？」と質問する
3. 選択されたテンプレート名（または新規作成の有無）を記録する

### 0-5. 歌詞テキストの選択/作成（Karaoke Style時は必須）

歌詞ディレクトリを確認し、対応する歌詞があるか確認する。

```
歌詞ディレクトリ: Remotion/my-video/public/assets/channels/acoriel/lyrics/
```

**手順:**
1. `ls` で歌詞ディレクトリ内のファイルを一覧表示する
2. 対応する歌詞ファイルがある場合 → ユーザーに「この歌詞を使いますか？」と確認
3. 歌詞ファイルがない場合 → ユーザーに「歌詞テキストを貼り付けてください」と依頼し、新規ファイルとして保存する

**適用条件:**
- `Karaoke Style`: 実行必須
- `Lyric Animation Style`: 必要な場合のみ実行（任意）

**歌詞ファイルの命名規則:**
- 音源と同じ名前で `.txt` 拡張子
- 例: 音源が `LA LA LA LOVESONG.mp3` → 歌詞は `LA LA LA LOVESONG.txt`

**歌詞フォーマット:**
```text
[イントロ]
ふっふっ…

[Aメロ]
回れ回れ merry-go-round
もう決して止まらないように

[サビ]
la la la la la love song
```

### 0-6. 選択結果のまとめ

素材選択後、以下を確認表示してからPhase 1に進む:
- 対象アカウント: `(選択されたアカウント)`
- 編集テンプレ: `(Karaoke Style / Lyric Animation Style)`
- Whisper実行: `(Yes/No)`
- 音源ファイル: `(選択されたパス)`
- 背景画像: `(選択されたパス)`
- エフェクト: `(選択されたテンプレート/設定)`
- 歌詞ファイル: `(選択されたパス or スキップ)`

---

## Phase 1: LRC + カラオケJSON生成

### 前提条件
- Python仮想環境: `Remotion/.venv/`（faster-whisper インストール済み）
- Phase 0で選択された音源・歌詞ファイル

### 手順

#### 1-1. スクリプトの実行

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- -u \
  "$TEAM_INFO_ROOT/.agent/skills/remotion/lyric-emotion-mapper/scripts/transcribe_to_lrc.py" \
  "<音源ファイルパス>" \
  --lyrics "<歌詞ファイルパス>" \
  --output "$TEAM_INFO_ROOT/Remotion/my-video/public/assets/<歌詞ファイル名と同名>.lrc" \
  --output-format lrc \
  --json "$TEAM_INFO_ROOT/Remotion/my-video/public/assets/lyric_animation_data.json" \
  --intro-label "(イントロ)" \
  --intro-min-seconds 0.30 \
  --model medium \
  --language ja
```

**SRTも同じスクリプトで生成する（推奨）**
```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- -u \
  "$TEAM_INFO_ROOT/.agent/skills/remotion/lyric-emotion-mapper/scripts/transcribe_to_lrc.py" \
  "<音源ファイルパス>" \
  --lyrics "<歌詞ファイルパス>" \
  --output "$TEAM_INFO_ROOT/Remotion/scripts/lyrics/<曲名>.srt" \
  --output-format srt \
  --intro-label "(イントロ)" \
  --intro-min-seconds 0.30 \
  --model medium \
  --language ja
```

※ `whisper ... --output_format srt` の直接実行では、先頭イントロ補助字幕が入らないため非推奨。  
このスクリプトは `LRC/SRT` の両方で「先頭イントロ + 歌い出し時刻合わせ」を行う。

**出力ファイル:**
| ファイル | 説明 |
|----------|------|
| `<歌詞ファイル名>.lrc` | LRC形式の歌詞（行レベルのタイムスタンプ） |
| `lyric_animation_data.json` | カラオケ用JSON（単語レベルのタイムスタンプ付き） |

**LRC命名ルール（必須）**
- LRCは必ず「歌詞ファイルと同名」で保存する。
- 例: `LALALA LOVESONG.txt` を使う場合 → `LALALA LOVESONG.lrc`
- 保存先は `Remotion/my-video/public/assets/`

**スクリプトオプション:**
| 引数 | 説明 | デフォルト |
|------|------|-----------|
| `--lyrics` | 歌詞テキストファイル（精度向上用プロンプト） | なし |
| `--output` | 出力LRCファイルパス | 音声と同名.lrc |
| `--output-format` (`--output_format`) | 出力形式 | `lrc` |
| `--json` | カラオケ用JSONの出力パス | なし（指定時のみ出力） |
| `--model` | Whisperモデルサイズ (`tiny`/`base`/`small`/`medium`/`large-v3`) | `medium` |
| `--language` | 言語コード | `ja` |
| `--intro-label` | イントロ表示テキスト | `(イントロ)` |
| `--intro-min-seconds` | この秒数以上の無歌唱区間があると先頭にイントロを自動挿入 | `0.30` |
| `--always-intro` | 先頭に必ずイントロを入れる | オフ |
| `--disable-intro` | イントロ自動挿入を無効化 | オフ |
| `--no-progress` | 進捗バーを無効化 | オフ |

**先頭表示ルール（必須）**
- `transcribe_to_lrc.py` は単語タイムスタンプを優先して、最初の歌詞開始時刻を検出する。
- 最初の歌詞開始が `--intro-min-seconds` 以上なら、`[00:00.00](イントロ)` を自動で入れる。
- これにより「最初はイントロ表示」「最初の歌詞は歌い出し時刻から表示」を標準化する。
- 誤判定時のみ手動でLRC先頭を調整する。

**進捗表示ルール（必須）**
- 実行コマンドは `python -u` を使い、進捗表示をリアルタイムで流す。
- スクリプトは `tqdm` で進捗バーを表示する（長時間処理でも止まって見えにくくする）。
- 進捗バーを消したい場合のみ `--no-progress` を使う。

#### 1-2. 生成ファイルの確認・修正 (自動チェック)

生成されたLRCファイルが元の歌詞と一致しているか、スクリプトで自動検証する。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/remotion/lyric-emotion-mapper/scripts/validate_lrc.py" \
  <出力LRCパス> \
  <歌詞テキストパス>
```

- **一致**: `✅ Success!` と表示されます。
- **不一致**: `⚠️ Mismatch detected` と表示され、差異が出力されます。手動でLRCを修正してください。

#### 1-3. 手動修正とJSON確認
- 自動チェックで問題がなければ、念のためLRCファイルのタイムスタンプを確認
- JSONの `label` フィールドに歌詞テキストのセクションラベルを反映
- 前奏/後奏など歌詞外区間がある場合は、`(イントロ)` / `(アウトロ)` の補助字幕を LRC と JSON に追加（先頭イントロは自動挿入が基本）

---

## Phase 2: 感情分析 & 演出設計

LRC/JSONファイルを読み込み、各行の感情を分析してアニメーションにマッピングする。

### テンプレ別の運用ルール

- `Karaoke Style`:
  `animation.in` は原則 `Karaoke` を使う。字幕可読性（2行分割、グロー、クロスディゾルブ）を優先し、必要最小限の例外のみ許可する。
- `Lyric Animation Style`:
  感情に応じて `animation.in/out` を積極的に使い分ける。

### 知識ベース: アニメーションと感情の対応

#### イン・アニメーション（登場）
| アニメーション | Remotion実装 | 感情的文脈 |
| :--- | :--- | :--- |
| **Karaoke** | 文字が左→右にハイライト（単語タイムスタンプ同期） | カラオケ風、歌に合わせた表示 |
| **SlideInLeft** | `translateX` -100% -> 0% | 自然な流れ、ストーリーテリング |
| **SlideInRight** | `translateX` 100% -> 0% | ダイナミック、エネルギー |
| **SlideInTop** | `translateY` -100% -> 0% | 新たな始まり、場面転換 |
| **SlideInBottom** | `translateY` 100% -> 0% | 強い意志、力強さ |
| **FadeInSlow** | `opacity` 0 -> 1 (duration: long) | 優しさ、静寂、悲しみ、深い愛 |
| **FadeInFast** | `opacity` 0 -> 1 (duration: short) | エネルギッシュ、注目 |
| **StaggeredFadeIn** | 文字ごとにdelayをずらす | 驚き、リズム感 |
| **PopIn** | `scale` 0 -> 1 (overshoot spring) | 衝撃、驚き、ポップさ |
| **Typewriter** | 1文字ずつ表示 | リズミカル、情報伝達 |
| **ScaleUp** | `scale` 0.5 -> 1 | 感情の高まり |
| **BlurIn** | `blur` 10px -> 0px | 神秘的、回想 |
| **ZoomIn** | `scale` 0 -> 1 | 迫力、劇的な瞬間 |

#### アウト・アニメーション（退場）
| アニメーション | Remotion実装 | 感情的文脈 |
| :--- | :--- | :--- |
| **BlurOut** | `blur` 0px -> 10px | メランコリック、余韻 |
| **FadeOut** | `opacity` 1 -> 0 | 終了、別れ |
| **CutOut** | 即座に非表示 | 断絶、テンポ重視 |
| **ScaleDown** | `scale` 1 -> 0 | 孤独、遠ざかり |
| **ZoomOut** | `scale` 1 -> 0.5 | 広がり、客観視 |

### 分析手順

1. **JSONを読み込む**: 各行のタイムスタンプとテキストを取得
2. **セクションを設定**: `label` にAメロ/Bメロ/サビ等を設定
3. **感情を特定**: 各行の支配的な感情を `emotion` に設定
4. **アニメーションを選定**: `animation.in` / `animation.out` を選択（デフォルトはKaraoke）

---

## Phase 3: Remotionへの反映

### 3-1. lyric_animation_data.json の構造

保存先: `Remotion/my-video/public/assets/lyric_animation_data.json`

```json
[
  {
    "time": 15.38,
    "duration": 4.14,
    "text": "回れ回れ merry-go-round",
    "label": "Aメロ",
    "emotion": "Energetic",
    "words": [
      { "word": "回", "start": 0.0, "end": 0.76 },
      { "word": "れ", "start": 0.76, "end": 1.1 },
      { "word": "回", "start": 1.1, "end": 1.36 },
      { "word": "れ", "start": 1.36, "end": 1.76 }
    ],
    "animation": {
      "in": "Karaoke",
      "out": "FadeOut",
      "props": {
        "inDurationFrames": 10,
        "outDurationFrames": 8
      }
    }
  }
]
```

**フィールド定義:**
| フィールド | 型 | 説明 |
|-----------|-----|------|
| `time` | number | 歌詞の開始時刻（秒） |
| `duration` | number | 歌詞の表示時間（秒） |
| `text` | string | 歌詞テキスト |
| `label` | string | セクションラベル（Aメロ/Bメロ/サビ等） |
| `emotion` | string | 感情（Gentle/Energetic/Melancholy/Determined/Joyful等） |
| `words` | array | 単語レベルのタイムスタンプ（カラオケモード用） |
| `animation.in` | string | イン・アニメーション名（`Karaoke`でカラオケ風） |
| `animation.out` | string | アウト・アニメーション名 |
| `animation.props` | object | アニメーション固有のパラメータ |

### 3-1.5 歌詞レイヤー実装チェック（必須）

Remotion反映時に次を満たすこと:

- 歌詞レイヤーにおける `<Sequence>` は1本（曲区間全体）
- 背景画像・補助字幕・効果音など非重複な同種レイヤーも、種類ごとに `<Sequence>` 1本で管理する
- 行選択ロジックがある（`songTime >= entry.time && songTime < entry.time + entry.duration`）
- `LyricLine` には行相対フレームを渡す（例: `lineFrame`）
- 既存アカウント実装が複数Sequence方式なら、反映時に1本化へ置換してから進行する
- 補助字幕 `(イントロ)` / `(アウトロ)` を使う場合は LRC と JSON の時刻・文言を一致させる
- 音源末尾は約0.5秒フェードアウト、CTA開始は音源終了約0.3秒前、末尾約2秒無音を守る

### 3-2. 音源参照の設定（コピー禁止）

音源は `Remotion/my-video/public/assets/channels/<channel>/songs/` に1つだけ配置し、`Root.tsx` の `defaultProps.audioAssetPath` で直接参照する。  
`Remotion/my-video/public/assets/audio.*` へのコピーは行わない。

### 3-3. Remotionでプレビュー

```bash
cd "$TEAM_INFO_ROOT/Remotion/my-video" && npx remotion studio
```

サイドバーで「AcoRielLyricCover」を選択してプレビュー。

**ローカル確認ルール（必須）**
- Phase 3 の完了条件は「`npx remotion studio` を起動し、対象Compositionをローカルで確認できる状態」にすること。
- 反映作業後は、原則ここで作業を止めてユーザー確認を待つ。

### 3-4. Remotionでレンダリング

```bash
bash "$TEAM_INFO_ROOT/Remotion/scripts/render_to_outputs.sh" AcoRielLyricCover <出力ファイル名>.mp4
```

**レンダリング実行ルール（必須）**
- レンダリングは勝手に実行しない。
- 実行前に必ずユーザー承認を取る。
- すぐ実行しない場合は、上記コマンドをそのままコピーできる形で提示する。

**レンダリング出力先ルール（必須）**
- 出力先は必ず `outputs/<channel>/renders/` に統一する。
- `Remotion/my-video/out/` は保存先として使わない。
- 既存の `out` / `renders` / `output` 出力がある場合は `outputs/` へ集約する。

---

## 使用方法（全体フロー）

```
Phase 0: アカウント選択 → テンプレ選択 → Whisper有無確認 → 音源/背景/エフェクト選択（毎回）→ 歌詞選択（Karaoke時必須）
Phase 1: (Whisper=Yes の場合) transcribe_to_lrc.py で LRC + カラオケJSON 生成
Phase 1.5: validate_lrc.py で歌詞の整合性チェック
Phase 2: JSONの感情・アニメーション情報を編集
Phase 3: 音源参照を設定（コピー禁止）→ Remotionプレビュー（ローカル確認）→ レンダリング（承認後のみ）
```

## ディレクトリ構成

```
Remotion/my-video/public/assets/channels/acoriel/
├── songs/          # 音源ファイル (.mp3)
├── lyrics/         # 歌詞テキスト (.txt)
└── backgrounds/    # 背景画像

Remotion/my-video/public/assets/
├── <歌詞ファイル名>.lrc         # 生成されたLRC（歌詞名と同名）
├── lyric_animation_data.json    # カラオケ用JSON
└── ...

outputs/acoriel/renders/
├── <出力ファイル名>.mp4         # AcoRielレンダリングの統一出力先
```
