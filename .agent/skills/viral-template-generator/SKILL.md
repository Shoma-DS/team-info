---
name: viral-template-generator
description: ショート動画を3層解析し、複数動画のパターンを統合分析して、オリジナルバズ動画を1から生成するスキル。
---

# viral-template-generator スキル

## 概要

バズ動画を解析してパターンを学習し、自分のオリジナル動画を1から生成するフルパイプライン。

```
[複数のバズ動画]
 → Phase 1: 動画解析（Python: カット/音声/バズ構造）→ analysis.json × N本
 → Phase A: 統合分析（Claude Agent）→ viral_patterns.md
 → Phase B: 素材数分析 → materials/ フォルダ作成
 → Phase C: テーマ提案 → ユーザー選択
 → Phase D: 台本 & 字幕生成 → script.md + subtitles.json
 → Phase E: 素材収集（ユーザーが materials/ に画像を入れる）
 → Phase F: Remotionテンプレート生成（画像スライドショー版）→ remotion/
```

## 絶対パスルール（必須）

- ユーザーにコマンドを渡すときは、必ず絶対パスで書く。
- リポジトリ内ファイルは `"$TEAM_INFO_ROOT/..."` の形で示す。
- ユーザー指定の入力先・出力先も `"[絶対パス]"` の形で案内する。

## トリガー条件

ユーザーが以下のいずれかを言った場合に起動する:
- 「動画を解析して」「動画を解析してテンプレを作って」
- 「バズテンプレを生成して」「バズ動画を作りたい」
- 「分析結果をまとめて」「パターンを分析して」
- 「テーマを提案して」「台本を作って」

**起動後は Phase 0 の判定から始める。**

## スキルディレクトリ

```
.agent/skills/viral-template-generator/
├── SKILL.md
├── README.md
├── scripts/
│   ├── setup.py              # 依存ライブラリインストール
│   ├── setup.sh              # POSIX ラッパー
│   ├── analyze_video.py      # メインCLI（3層解析 + JSON生成）
│   └── layers/
│       ├── video_structure.py
│       ├── speech_analysis.py
│       └── viral_pattern.py
└── template/                 # Remotionベーステンプレート
    ├── package.json
    ├── tsconfig.json
    ├── remotion.config.ts
    └── src/
        ├── index.ts
        ├── Root.tsx
        ├── ViralVideo.tsx     # Claude が生成するメインコンポーネント
        ├── types.ts
        └── components/
            ├── Scene.tsx       # 元動画クリップ用
            ├── ImageScene.tsx  # 静止画（Ken Burns）用 ← 新規
            ├── Subtitle.tsx
            ├── ZoomEffect.tsx
            └── Hook.tsx
```

## 出力ディレクトリ構造

```
inputs/viral-analysis/output/
[パターン名]_YYYYMMDD/                 ← 分析バッチ（同日2回目は [パターン名]_YYYYMMDD_2）
    ├── [参照動画1タイトル]/            ← Phase 1 の出力（analyze_video.py が生成）
    │   └── analysis.json
    ├── [参照動画2タイトル]/
    │   └── analysis.json
    ├── viral_patterns.md               ← Phase A: 統合分析レポート
    ├── script.md                       ← Phase D: 台本
    ├── subtitles.json                  ← Phase D: 字幕タイムライン
    ├── materials/                      ← Phase E: 素材フォルダ
    │   ├── 00_hook.jpg
    │   └── ...
    └── （Remotion は my-video に統合）
```

**重要**: analysis.json は `output/[パターン名]_YYYYMMDD/{動画名}/analysis.json` に格納される。
Phase A では使用する分析バッチフォルダをユーザーに確認してから読み込む。

---

## 動画フォルダ構成

```
inputs/viral-analysis/
├── 未分析/          ← 参考にしたいバズ動画をここに置く（分析前）
├── 分析済み/        ← 解析完了した動画をテンプレ名ごとに格納
│   ├── アダルトアフィリ/
│   │   ├── 参考動画A.mp4
│   │   └── 参考動画B.mp4
│   └── 芸能人エンタメ/
│       └── 参考動画C.mp4
└── output/          ← 分析結果・台本・字幕・素材
    └── [パターン名]_YYYYMMDD/
```

- 動画を `inputs/viral-analysis/未分析/` に置くだけで候補として認識される
- 解析完了後、`分析済み/[パターン名]/` フォルダに移動する（フォルダがなければ自動作成）
- パターン名は Phase 1 実行時に確定したものを使う

---

## Phase 0: 起動判定

起動時に各フォルダをスキャンし、状態をユーザーに提示してから何をするか選ばせる。

**Step 0-1: 状態を自動スキャン**

以下を確認する:

1. `inputs/viral-analysis/未分析/` 内の動画ファイル一覧（`.mp4` / `.mov` 等）
2. `inputs/viral-analysis/分析済み/` 内の動画ファイル一覧
3. `inputs/viral-analysis/output/` 内の分析バッチフォルダ一覧と各状態
   （`viral_patterns.md` / `script.md` / `materials/` 内の画像 があるか）
4. `Remotion/my-video/src/viral/` 内の既存 TSX ファイル一覧

**Step 0-2: 状態をユーザーに提示して選択させる**

```
📊 現在の状態:

【既存テンプレ（すぐ使える）】
  - アダルトアフィリ/ガチで脱いだ女性芸能人3選_20260313.tsx
  - ...

【分析バッチ】
  - アダルトアフィリ_20260312/ ✅ viral_patterns.md あり / ❌ script.md なし
  - ...

【未分析の動画】（inputs/viral-analysis/未分析/）
  - 参考動画A.mp4
  - 参考動画B.mp4
  - ...（なければ「なし」と表示）

---

何をしますか？

  A) 既存テンプレで新規動画を作る
  B) 分析を上書きする（既存テンプレを選んで分析からやり直し）
  C) 新しい分析から動画を作る（未分析フォルダの動画を解析）
  D) 途中から再開する（フェーズを選んでやり直し）
```

**A を選んだ場合:**

1. 既存テンプレ一覧を提示して選ばせる
2. 新しい動画のテーマ・タイトルを聞く
3. プラットフォーム（tiktok / shorts / reels）を確認

確認後、Phase C へ進む。

**B を選んだ場合:**

1. 既存テンプレ一覧を提示して、上書きするテンプレを選ばせる
2. 未分析フォルダの動画一覧を提示して、解析する動画を選ばせる
3. パターン名（分析バッチ名）を確認

確認後、Phase 1 → Phase A と実行し、既存の分析バッチを上書き。

**C を選んだ場合:**

1. 未分析フォルダの動画一覧を提示して、解析する動画を選ばせる
   （複数選択可。「全部」と言えば全件）
2. パターン名と対象プラットフォームを確認

確認後、Phase 1 → 全フロー実行。解析完了した動画は `分析済み/[パターン名]/` へ移動する。

**D を選んだ場合:**

1. どの分析バッチ / 既存テンプレを対象にするかを選ばせる
2. 全フェーズのステップ一覧をユーザーに提示する:

```
📋 フェーズ一覧:

  Phase A  — 統合分析（analysis.json → viral_patterns.md 生成）
  Phase B  — 素材フォルダ作成（materials/ と README.md）
  Phase C  — テーマ提案・選択
  Phase D1 — 台本生成（script.md）
  Phase D2 — ひらがな台本生成・辞書登録（script_hiragana.md）
  Phase D3 — 字幕生成（subtitles.json）
  Phase D4 — 音声生成（VOICEVOX → narration.wav）
  Phase E  — 素材収集（Wikimedia自動取得 + 手動配置）
  Phase F  — Remotionテンプレート生成（TSX + Root.tsx）
  Phase G  — ジェットカット（無音短縮）
  Phase H  — レンダリング

どのフェーズからやり直しますか？（例: "Phase E から" / "D3から"）
```

3. 指定されたフェーズから処理を再開する。それより前のフェーズの成果物はそのまま引き継ぐ。

---

## Phase 1: 動画解析（Python）

### セットアップ（自動処理・Claude は何もしなくてよい）

`analyze_video.py` 起動時に自動判定・実行される:
- フラグファイル: macOS/Linux=`~/.config/viral-template-generator/.setup_done`, Windows=`%APPDATA%/viral-template-generator/.setup_done`
- なければ setup.py を自動実行してフラグを書き込む

### インボックスフォルダ

```
inputs/viral-analysis/
```

引数なしで起動すると動画一覧が表示され選択できる。

### Step 1-1: 解析実行

**推奨（対話モード）**: 起動フローが対話式で new/use_existing/overwrite を選ばせる。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/analyze_video.py"
```

**一括解析（全動画を今日の日付フォルダへ）:**

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/analyze_video.py" \
  --all --platform [tiktok|shorts|reels] \
  --pattern-name [パターン名]
```

**単体指定（非対話）:**

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/analyze_video.py" \
  "[入力動画の絶対パス]" \
  --platform [tiktok|shorts|reels] \
  --pattern-name [パターン名] \
  --date [YYYYMMDD]   # 省略すると今日の日付
```

完了したら「終わりました」と伝えるよう案内する。

**出力先**: `inputs/viral-analysis/output/[パターン名]_YYYYMMDD/{動画名}/analysis.json`

### Step 1-2: 解析完了後 — 動画を分析済みフォルダへ移動

解析が完了したら、対象動画を `分析済み/[パターン名]/` へ移動する。
フォルダが存在しない場合は自動作成する。

```bash
PATTERN_NAME="[パターン名]"  # 例: アダルトアフィリ
SRC="$TEAM_INFO_ROOT/inputs/viral-analysis/未分析/[動画ファイル名]"
DEST_DIR="$TEAM_INFO_ROOT/inputs/viral-analysis/分析済み/$PATTERN_NAME"

mkdir -p "$DEST_DIR"
mv "$SRC" "$DEST_DIR/"
```

複数動画を解析した場合は、選択した全動画に対して同じ移動処理を行う。

### クロスプラットフォーム通知

| OS      | 通知方式                                   |
|---------|--------------------------------------------|
| macOS   | `osascript` 通知センター + サウンド        |
| Linux   | `notify-send`（libnotify）+ ターミナルベル |
| Windows | PowerShell タスクトレイ BalloonTip + beep  |

---

## Phase A: 統合分析（Claude Agent）

**目的**: 複数の analysis.json を横断的に分析し、バズ動画の共通パターンを抽出して `viral_patterns.md` を生成する。

### Step A-0: 分析バッチフォルダの確認

Phase 0 の判定で選択された分析バッチフォルダ（例: `芸能人エンタメ_20260311`）を使う。
ユーザーに確認してからそのフォルダ内の analysis.json を読み込む。

```
inputs/viral-analysis/output/[パターン名]_YYYYMMDD/
├── 動画1/analysis.json
├── 動画2/analysis.json
└── ...
```

Phase A 以降の出力（`viral_patterns.md`, `script.md`, `subtitles.json`, `materials/` など）は
**同じ分析バッチフォルダ直下**に保存する。

### Step A-1: analysis.json を全件読み込む

`inputs/viral-analysis/output/[パターン名]_YYYYMMDD/` 以下のすべての `analysis.json` を Read ツールで読み込む。
（分析バッチフォルダ内の直下サブフォルダを対象とする）

各ファイルから以下を抽出する:
- `duration`, `fps`, `platform`
- `video_structure.cuts` → カット数・各カット尺
- `video_structure.text_regions` → 字幕位置分析用（下記の字幕スタイル解析に使う）
- `speech_structure.transcript` → セグメント数・文字数・表示時間
- `speech_structure.words_per_minute`
- `speech_structure.emotional_intensity`
- `viral_structure.hook_time`, `hook_type`
- `viral_structure.pattern_interrupts` → 回数・タイミング
- `viral_structure.tone`, `information_density`
- `audio_scene.bgm_segments` → BGM区間リスト（start/end/energy）
- `audio_scene.sfx_events` → 効果音イベント（time/type/energy）
- `audio_scene.dominant_tempo` → テンポ（BPM）
- `audio_scene.music_coverage` → BGMが占める割合（0-1）
- `audio_scene.energy_timeline` → 音量の時系列（0.5秒ごと）

**字幕スタイル解析（AIレビュー優先）:**

`analyze_video.py` は各動画フォルダに以下を出力する:

- `subtitle_style_samples/manifest.json`
  字幕スタイルが変わった可能性が高いカットごとの代表スクショ一覧
- `subtitle_style_samples/REVIEW.md`
  画像パスと確認ポイント
- `subtitle_style_template.json`
  AIエージェントが実際に見て埋める雛形

`subtitle_visual` の数値（色・ストローク・座布団・Y位置）は**補助情報**として使ってよい。
ただし `fontFamily` / `fontWeight` / `fontSize` は、必ずスクショを見て判断する。

### Step A-2: 統計計算

以下の統計を計算する:

| 指標 | 計算方法 |
|---|---|
| 平均尺 | 全動画の duration の平均 |
| 平均カット数 | 全動画の cuts.length の平均 |
| 平均カット尺 | 全カットの (end-start) の平均 |
| フック別動画数 | hook_type ごとにカウント |
| パターンインタラプト平均回数 | pattern_interrupts.length の平均 |
| 字幕セグメント平均数 | transcript.length の平均 |
| 字幕平均文字数 | 全セグメントの text.length の平均 |
| 字幕平均表示時間 | 全セグメントの (end-start) の平均 |
| 字幕最短表示時間 | min(end-start) |
| 字幕最長表示時間 | max(end-start) |
| 字幕Y位置（text_regions avg_y × 100） | subtitle_visual.yPercent が取れない場合のみ使う（後述） |
| 字幕配置ゾーン | top / middle / bottom |
| **座布団ありの動画数** | background_box_detected=true の本数 |
| **ストロークありの動画数** | stroke_detected=true の本数 |
| **推奨字幕スタイル** | 下記ルールで決定（後述） |
| 話速（wpm） | speech_structure.words_per_minute |
| 感情強度 | speech_structure.emotional_intensity |
| BGM区間数 | audio_scene.bgm_segments.length |
| BGMカバー率（%） | audio_scene.music_coverage × 100 |
| 平均テンポ（BPM） | audio_scene.dominant_tempo |
| 効果音イベント数 | audio_scene.sfx_events.length |
| 効果音タイプ分布 | sfx_events の type ごとにカウント（impact/chime/whoosh/transition） |
| 効果音と発話の関係 | sfx_events の time と transcript の発話区間を照合し「発話中」「無音時」「カット点」を判定 |
| 時間構成の分割 | 全体を3分割（フック/本編/CTA）でそれぞれの平均尺 |

### Step A-3: 台本構成パターンの特定

各動画の transcript を読んで以下を特定する:
- フック（最初の発話）の特徴: 疑問形/断言/数字列挙 など
- 本編の繰り返しパターン: Nエピソード構成か、時系列か、比較か
- 締め・CTA の特徴
- 特徴的なワードや言い回し

### Step A-4: viral_patterns.md を生成

**出力先**: `inputs/viral-analysis/output/[パターン名]_YYYYMMDD/viral_patterns.md`

生成内容のテンプレート:

```markdown
# バズ動画パターン分析レポート
生成日: YYYY-MM-DD
分析本数: N本

---

## 1. 基本統計

| 指標 | 平均 | 最小 | 最大 |
|---|---|---|---|
| 動画尺（秒） | X | X | X |
| カット数 | X | X | X |
| 1カット平均尺（秒） | X | X | X |
| 字幕セグメント数 | X | X | X |
| 字幕1件あたり文字数 | X | X | X |
| 字幕1件あたり表示時間（秒）| X | X | X |
| パターンインタラプト回数 | X | X | X |

---

## 2. 時間構成（3分割）

| セクション | 平均開始(s) | 平均終了(s) | 平均尺(s) | 役割 |
|---|---|---|---|---|
| フック | 0 | X | X | 掴み・驚き・疑問提示 |
| 本編 | X | X | X | エピソード・情報展開 |
| アウトロ/CTA | X | 末尾 | X | まとめ・フォロー促し |

---

## 3. フック分析

- 最多フックタイプ: `statement` / `question` / `visual`
- フックタイプ分布: statement X件, question X件, visual X件
- 共通フックパターン:
  - 「[数字] 選」「まさかの〜」「〜した結果」などの定型
  - 断言で始まり疑問で終わるパターン

---

## 4. パターンインタラプト（視聴者を飽きさせない仕掛け）

- 平均回数: X回 / 動画
- 典型タイミング: 開始から X秒, X秒, X秒 付近
- 密度: X秒ごとに1回

---

## 5. 字幕スタイル詳細分析

### タイミング
| 指標 | 値 |
|---|---|
| 平均表示時間 | Xs / セグメント |
| 最短表示時間 | Xs |
| 最長表示時間 | Xs |
| 平均文字数 | N文字 / セグメント |
| 推奨最大文字数 | N文字（20文字以内推奨） |
| 話速 | Xwpm |

### 位置
| 指標 | 値 |
|---|---|
| Y位置（画面内%） | X%（0=上端, 100=下端） |
| 配置ゾーン | top / middle / bottom |
| 水平位置 | center（中央揃え） |

### ビジュアルスタイル（スタイルテンプレートを使う）

**重要: フォント系の最終判断は `subtitle_style_template.json` を見て行う。`subtitle_visual` は補助であり、固定フォントを決め打ちしない。**

#### Step 1: 各動画のレビュー雛形を確認する

各 `analysis.json` と同じフォルダにある `subtitle_style_template.json` を開く。
`status != approved` のときは、同フォルダの `subtitle_style_samples/manifest.json` と `subtitle_style_samples/REVIEW.md` を読み、
代表スクショ (`*_crop.jpg` / `*_full.jpg`) を見て以下を埋める:

- `subtitle.fontFamily`
- `subtitle.fontWeight`
- `subtitle.fontSizePx1920h`
- `subtitle.textColor`
- `subtitle.strokeWidthPx` / `subtitle.strokeColor`
- `subtitle.background`
- `subtitle.paddingH` / `subtitle.paddingV` / `subtitle.borderRadius`
- `subtitle.yPercent`
- `subtitle.lineColors`
- 必要なら `hook.*`

レビューが終わったら `status: approved` に更新する。

#### Step 2: スタイルテンプレートの選択

全動画のレビュー済み `subtitle_style_template.json` を集計し、最も多い字幕本文スタイルをベースにする。
ただし hook / name card は別スタイルなら分離してよい。

テンプレートファイル: `$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/config/subtitle_styles.json`

既存テンプレートに近い場合:
- `background` が多数派 → `bg_box_entertainment`
- `strokeWidthPx` が多数派で `background` なし → `stroke_entertainment`
- どちらでもない → `plain_light`

既存テンプレートに合わない場合:
- `viral_patterns.md` に「新規カスタムスタイル」として明記し、
- Phase F ではレビュー済み値をそのまま `SUBTITLE_STYLE` に反映する

#### Step 3: 数値の決定ルール

- `fontFamily`: スクショを見て判断した最頻値を採用
- `fontSize`: `subtitle.fontSizePx1920h` の中央値
- `yPercent`: `subtitle.yPercent` の中央値
- `color`: `subtitle.textColor` の最頻値
- `background`: `subtitle.background` の最頻値
- `strokeWidth` / `strokeColor`: レビュー済み値の中央値 / 最頻値
- `lineColors`: 交互配色がある場合のみ採用

空欄が残る場合のみ `subtitle_visual` の実測値で補完してよい。
それも取れない場合だけ platform default を使う。

#### 適用例（viral_patterns.md に記載する）

```markdown
## 11. 推奨字幕スタイル

- **テンプレート**: `bg_box_entertainment`
- **レビュー元**: 7本中5本の `subtitle_style_template.json`
- **フォント**: Hiragino Sans
- **フォントサイズ**: 48px
- **文字色**: #ebc1b9
- **座布団色**: rgba(22,14,14,0.88)
- **Y位置**: 70%
- **補足**: hook は角ゴ・交互配色で別管理
```

**Phase F の TSX 生成では必ずこのセクションと `subtitle_style_template.json` を見てから `SUBTITLE_STYLE` を生成すること。**

---

## 6. 台本構成パターン（ベストプラクティス）

1. **フック（0〜Xs）**: 結論・驚き・数字を冒頭に置く
   - 例: 「〇〇した芸能人X選」「まさかの〜」
2. **予告（X〜Xs）**: 全体の内容を数秒で予告
3. **本編（X〜Xs）**: Xエピソード構成（各エピソードX秒）
   - エピソードごとに小さな驚きや笑いを入れる
   - パターンインタラプトを X 秒間隔で挿入
4. **まとめ/CTA（X〜末尾）**: 締めのコメント + フォロー促し（控えめに）

---

## 7. 必要素材数の目安

素材はすべて縦型（1080×1920, 9:16）で準備する。

| 用途 | 必要枚数 | ファイル名規則 |
|---|---|---|
| フック背景 | 1枚 | `00_hook.jpg` |
| 予告背景 | 1枚 | `01_opening.jpg` |
| 本編セクションごと | X枚（1セクション=X枚） | `02_s1_1.jpg` 〜 |
| CTA背景 | 1枚 | `99_cta.jpg` |
| **合計** | **約X枚** | |

---

## 8. バズ要因まとめ（共通点）

- [分析から読み取れたバズ要因を箇条書きで]
- 例: 芸能人や有名人を絡める、驚き・スキャンダル要素、コンパクトな情報量

---

## 9. 推奨クリエイティブ方針

このパターンを参考に新規動画を作る際の指針:
- [具体的な推奨事項を列挙]

---

## 10. BGM・効果音分析

### BGM
| 指標 | 値 |
|---|---|
| BGMカバー率 | X%（全体の何%がBGMか） |
| 平均テンポ | X BPM |
| エネルギー傾向 | high / medium / low |
| BGM区間パターン | 通し / フェードイン / セクション切り替えで変化 等 |

**BGM区間タイムライン（代表例）:**
| 開始(s) | 終了(s) | エネルギー | 備考 |
|---|---|---|---|
| X | X | high | フック・オープニング |
| X | X | medium | 本編落ち着き部分 |
| X | X | high | CTA・エンディング |

### 効果音（SFX）
| 指標 | 値 |
|---|---|
| 合計イベント数 | N回 |
| タイプ分布 | impact X件 / chime X件 / whoosh X件 / transition X件 |
| 発火タイミングの傾向 | カット点 / パターンインタラプト / 字幕出現時 |

**効果音タイムライン（代表例）:**
| 時刻(s) | タイプ | エネルギー | 発火コンテキスト |
|---|---|---|---|
| X | impact | X | カット切り替え |
| X | chime | X | 字幕ポップアップ |
| X | transition | X | セクション間 |

### 音楽的特徴まとめ
- BGMは[常時流れる/サビのみ/無音あり]
- SFXは[カット毎/インタラプト毎/字幕ごと]に挿入される
- テンポX BPMの[アップビート/落ち着いた/ドラマチック]な楽曲
- 新規動画の推奨BGM: [雰囲気・ジャンルの指定]
- 推奨SFXセット: [必要な効果音の種類と挿入タイミング]

---

## 11. 推奨字幕スタイル

> Phase F の TSX 生成時に必ずここを読み込んで `SUBTITLE_STYLE` を組み立てること。

### スタイルテンプレート選択

- 座布団あり動画数: X / N本
- ストロークあり動画数: X / N本
- **→ 採用テンプレート: `[bg_box_entertainment / stroke_entertainment / plain_light]`**
  （`$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/config/subtitle_styles.json` 参照）

### 適用パラメータ

| パラメータ | 値 | 根拠 |
|---|---|---|
| テンプレート名 | `[テンプレート名]` | レビュー済み template の多数派 |
| fontSize | Xpx | `subtitle_style_template.json` の中央値 |
| color | `#XXXXXX` | レビュー済み textColor の最頻値 |
| background | `rgba(R,G,B,A)` | レビュー済み background の最頻値 |
| yPercent | X% | レビュー済み yPercent の中央値 |
| fontFamily | `[実際のフォント名]` | スクショレビューで判断 |
| strokeWidth | Xpx or null | レビュー済み strokeWidthPx |
| strokeColor | `#XXXXXX` or null | レビュー済み strokeColor |
```

---

## Phase B: 素材数分析 & フォルダ作成

**目的**: viral_patterns.md の統計から必要素材数を確定し、materials/ フォルダと命名規則ガイドを作成する。

### Step B-1: 必要素材数の確定

`viral_patterns.md` の「7. 必要素材数の目安」に基づき、以下を決定する:
- フック用: 1枚
- 予告用: 1枚
- 本編セクション数: N（分析から算出）× 各セクションあたり枚数
- CTA用: 1枚
- 合計: M枚

### Step B-2: フォルダ & ガイド作成

以下のフォルダとファイルを作成する:

```
inputs/viral-analysis/output/[パターン名]_YYYYMMDD/
└── materials/
    └── README.md    ← 収集ガイド
```

`materials/README.md` の内容:
```markdown
# 素材フォルダ

ここに画像・動画素材を入れてください。

## 必要素材一覧

| ファイル名 | 用途 | イメージ |
|---|---|---|
| 00_hook.jpg | フック背景 | [説明] |
| 01_opening.jpg | 予告背景 | [説明] |
| 02_s1_1.jpg | セクション1 カット1 | [説明] |
| ... | ... | ... |
| 99_cta.jpg | CTA背景 | [説明] |

## 素材規格
- サイズ: 1080×1920px（縦型 9:16）
- 形式: .jpg / .png / .mp4（短い動画ループも可）
- 注意: 著作権フリー素材を使用してください
  - 推奨: Unsplash, Pexels, Pixabay, Adobe Stock フリー素材

## ファイルを入れたら Claude に「素材を入れました」と伝えてください
```

---

## Phase C: テーマ提案 & 選択

**目的**: viral_patterns.md の台本構成パターンを参考に、新規コンテンツのテーマ候補を3〜5つ提案する。

### Step C-1: 既存パターンとユーザーのジャンルを確認

ユーザーに以下を確認する:
- 作りたいジャンル・ニッチは何か（例: 芸能、ビジネス、健康など）
- 対象プラットフォーム（TikTok / Shorts / Reels）
- ターゲット視聴者

### Step C-2: テーマ候補を生成・提案

分析したフックパターン・台本構成・toneに基づき、候補を生成する。

各候補に以下を含める:
```
## 候補 [N]: [タイトル案]

- **ターゲット**: [視聴者像]
- **フック（冒頭3秒）**: [具体的な文章]
- **本編構成**:
  1. [セクション1: 内容の概要]
  2. [セクション2: 内容の概要]
  3. [セクション3: 内容の概要]
- **CTA**: [締めの一文]
- **想定バズ理由**: [なぜバズるか]
- **必要な素材イメージ**: [どんな画像が必要か]
```

### Step C-3: ユーザーの選択を待つ

「上記からひとつ選んでください（または「N番」と言ってください）」と伝えて入力を待つ。

---

## Phase D: 台本 & 字幕生成

**目的**: 選択されたテーマをもとに、viral_patterns.md のパターンに従って台本と字幕タイムラインを生成する。

### Step D-1: script.md を生成

**出力先**: `inputs/viral-analysis/output/[パターン名]_YYYYMMDD/script.md`

生成フォーマット:
```markdown
# 台本: [タイトル]
プラットフォーム: [platform]
想定尺: [Xs]
作成日: YYYY-MM-DD

---

## フック（0〜3秒）

[フック文章。断言または驚き。20文字以内を推奨]

---

## 予告（3〜6秒）

[全体の内容を一言で予告]

---

## 本編 セクション1: [テーマ]（6〜20秒）

[内容。話し言葉で。句点ごとに改行推奨]

---

## 本編 セクション2: [テーマ]（20〜35秒）

[内容]

---

## 本編 セクション3: [テーマ]（35〜50秒）

[内容]

---

## アウトロ/CTA（50〜58秒）

[締めのコメント。フォロー促しは控えめに1回だけ]

---

## 演出メモ

- パターンインタラプト: [X秒、X秒 付近に挿入]
- フックタイプ: [statement/question/visual]
- トーン: [entertainment/educational/curiosity]
```

### Step D-2: 台本校正（AI自動レビュー）

**目的**: script.md の誤字脱字・意味の通らない文・字数バランスを自動チェックして修正する。

Claude が以下の観点で script.md を読んでレビューする:

| チェック項目 | 基準 |
|---|---|
| 誤字脱字 | 明らかな変換ミス・脱字 |
| 意味の通らない文 | 文脈から外れた表現・主語述語のねじれ |
| 文体統一 | 「だ・である」「です・ます」混在の排除 |
| フックの強度 | 冒頭3秒で視聴者を引き込めるか（viral_patterns.md の statement パターンに合っているか） |
| 字数バランス | 各セクションが想定尺（1文字≒0.12秒）に収まるか |
| 重複表現 | 同じ言葉・フレーズの繰り返し |

**修正ルール:**
- 誤字脱字・明らかな文法ミスは **自動修正して script.md を上書き**
- 内容・フレーズの変更が必要な場合は **修正案を提示してユーザーに確認**
- 修正後は「校正完了。X箇所修正しました」と報告する

---

### Step D-3: ひらがな台本生成（VOICEVOX 読み間違い防止）

**目的**: VOICEVOX が漢字を誤読しないよう、台本をひらがなに変換した `script_hiragana.md` を生成する。

#### Step D-3-1: 自動変換

```bash
"$TEAM_INFO_ROOT/Remotion/.venv/bin/python3.11" \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/convert_to_hiragana.py" \
  --script "[script.mdの絶対パス]"
```

`script_hiragana.md` が同フォルダに生成される。

#### Step D-3-1.5: 辞書の更新（人名・作品名は必須）

- 共通の誤読対策語は `"$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/config/pronunciation_dictionary.json"` に登録する
- 企画固有の人名・作品名・地名は `script.md` と同じフォルダの `reading_dictionary.json` に登録する
- `reading_dictionary.json` には `surface` と `reading` を必ず入れ、`source_url` や `source_note` を残してよい
- VOICEVOX 用に読みを強制したいときは `voice_text` を併記してよい
  例: `清純派` → `reading: せいじゅんは`, `voice_text: せいじゅんハ`
- 人名・作品名は Web で表記と読みを確認してから登録する
- 字幕に出す固有名詞は `script.md` と `subtitles.json` の両方で同じ表記になっているか確認する

#### Step D-3-2: Claude によるレビューと修正（必須）

自動変換後、Claude が `script_hiragana.md` を読み込んで以下を確認・修正する:

| チェック項目 | よくある誤変換例 | 正しい読み |
|---|---|---|
| 人名・芸能人名 | `しゅつみ`（出身） | `しゅっしん` |
| 動詞の誤読 | `ちょうんだ`（挑んだ） | `いどんだ` |
| 複合語 | `じょゆうたましい` | `じょゆうだましい` |
| 外来語・カタカナ | そのまま残っていればOK | - |
| 固有名詞 | 人名・地名・作品名が正しく読まれているか | - |

誤変換を発見した場合は、まず辞書に登録し、そのうえで `script_hiragana.md` を再生成する。必要なら最終調整として `script_hiragana.md` を直接編集して修正する。
修正後「ひらがな台本の確認が完了しました」と報告する。

---

### Step D-4: subtitles.json を生成

**出力先**: `inputs/viral-analysis/output/[パターン名]_YYYYMMDD/subtitles.json`

字幕タイミングの計算方法:
- 参照動画の平均話速（words_per_minute）から1文字あたりの表示時間を算出
- 1セグメントあたり平均X文字・Y秒を参考値とする
- セクション境界（フック終わり、本編切り替え）でセグメントを分割する

#### Step D-4-0: 字幕の行数制限（必須）

subtitles.json 生成後、必ず `split_subtitles.py` で **2行以内** に収める:

```bash
"$TEAM_INFO_ROOT/Remotion/.venv/bin/python3.11" \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/split_subtitles.py" \
  --input "[subtitles.jsonの絶対パス]" \
  --mode newline
```

- 13文字以内 → そのまま
- 14文字以上 → **GiNZA で文/文節区切り** → 改行を入れる
- フック以外で3行以上になる場合 → **2行以内で次の字幕セグメントへ持ち越す**
- split モードは各行を独立した時間セグメントにする

#### Step D-4-0.5: 固有名詞ルール（必須）

**人名・映画名・作品名などの固有名詞は、必ず1エントリ（1画面）に収める。**
複数エントリに分割してはならない。

| ルール | 詳細 |
|---|---|
| 1エントリ完結 | 人名・映画名・作品名が1エントリを跨いではいけない。名前の一部が前のエントリ、残りが次のエントリに分かれるのは禁止 |
| 括弧「」の改行位置 | `「` の直後で改行しない。`「` は改行後の行頭に来るよう、改行は `「` の手前に入れる |
| 括弧付き固有名詞が長すぎる場合 | 括弧「」を付けると1行に収まらない場合は、括弧を省略してよい（字幕で括弧は必須ではない） |

**判定フロー:**

```
固有名詞を検出 → 1エントリに入る？
  ├─ YES → そのまま
  └─ NO → 1エントリに結合し、必要なら \n で2行以内に分割
           └─ 1行に収まらない文字列に「が含まれる場合:
               ├─ 括弧を行頭に移動して改行を調整
               └─ それでも収まらなければ括弧を省略
```

**悪い例 / 良い例:**

```
# NG: 映画タイトルが2エントリに分割されている
{ from: 642, to: 677, text: "映画\n「愛の" },      ← 「愛の」だけ
{ from: 677, to: 733, text: "流刑地」\nで見せた" }, ← 「流刑地」だけ

# OK: 映画タイトルが1エントリに収まっている（括弧を省略）
{ from: 642, to: 710, text: "映画\n愛の流刑地" },   ← タイトル全体が1画面
{ from: 710, to: 733, text: "で見せた" },
```

生成フォーマット:
```json
{
  "fps": 30,
  "total_duration_seconds": 58.0,
  "total_frames": 1740,
  "segments": [
    {
      "id": 1,
      "section": "hook",
      "from_time": 0.0,
      "to_time": 3.0,
      "from_frame": 0,
      "to_frame": 90,
      "text": "[フック文章]"
    },
    {
      "id": 2,
      "section": "opening",
      "from_time": 3.0,
      "to_time": 6.0,
      "from_frame": 90,
      "to_frame": 180,
      "text": "[予告文章]"
    }
  ]
}
```

タイミング設計の目安:
- 1文字 = 約0.1〜0.15秒（参照動画の話速に合わせる）
- セグメントの最小表示時間: 1.5秒
- セグメントの最大表示時間: 6秒（長い文章は2分割）
- パターンインタラプトの直前後はセグメントを区切る

### Step D-4: VOICEVOX 音源化

**目的**: script.md のナレーション部分を VOICEVOX で音声化し、Remotion プロジェクトに配置する。

#### Step D-4-1: プロファイル選択

エンタメ系動画には以下を推奨:

| プロファイル名 | 声 | 特徴 |
|---|---|---|
| `narrator_female` | 四国めたん・ノーマル | 明るく聞き取りやすい（推奨） |
| `zundamon_normal` | ずんだもん・ノーマル | 元気でカジュアル |
| `narrator_male` | 雨晴はう・ノーマル | 落ち着いた男性ナレーター |
| `aoyama_ryuusei_normal` | 青山龍星・ノーマル | 重厚な男性ナレーター |

ユーザーに確認するか、「推奨で進めます」と伝えてデフォルト（`aoyama_ryuusei_normal`）を使う。

#### Step D-4-2: 音源生成コマンド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/generate_viral_voice.py" \
  --script "[script_hiragana.mdの絶対パス]" \
  --output-dir "$TEAM_INFO_ROOT/Remotion/my-video/public/viral/[タイトル]/audio" \
  --profile [プロファイル名] \
  --timeline-ts "$TEAM_INFO_ROOT/Remotion/my-video/src/viral/generated/[任意のファイル名].ts"
```

**`script_hiragana.md` を `--script` に指定する（Step D-3 で生成したひらがな台本）。**
`generate_viral_voice.py` は `--script` に `script_hiragana.md` を渡すと自動でそれを使う。
`script.md` を渡した場合でも同フォルダに `script_hiragana.md` があれば自動優先される。

- GUI 版ではなく Docker 上の `VOICEVOX Engine` を使う
- 事前確認は `python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" voicevox-engine-status`
- `run-remotion-python` から起動する場合、必要なら `start-voicevox-engine` が自動で補助される
- 明示的に起動する場合は `python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" start-voicevox-engine`
- `subtitles.json` が同じフォルダにあれば、音声生成後に先頭無音を見て字幕開始を自動補正する
- `--timeline-ts` を渡すと、Remotion 側で使う `SUBTITLE_TIMELINE` の TS モジュールも同時に更新される

#### Step D-4-3: 出力ファイル

```
remotion/public/audio/
└── narration.wav       ← 全セクション結合済みの1ファイル
```

個別セクションも生成される（デバッグ用）:
```
remotion/public/audio/
├── 00_hook.wav
├── 01_opening.wav
├── 02_s1.wav
├── 03_s2.wav
├── 04_s3.wav
├── 05_cta.wav
└── narration.wav       ← 上記を結合
```

#### Step D-4-4: ViralVideo.tsx への Audio 追加

音源生成後、ViralVideo.tsx に以下を追加する:

```typescript
import { Audio, staticFile } from "remotion";

// ViralVideo コンポーネント内に追加
<Sequence from={0} durationInFrames={totalFrames}>
  <Audio src={staticFile("audio/narration.wav")} volume={1.0} />
</Sequence>
```

---

### Step D-5: 台本・字幕・音源のレビューを促す

生成後、ユーザーに以下を伝える:
- `script.md`（校正済み台本）
- `subtitles.json`（GiNZA 折り返し済み）
- `remotion/public/audio/narration.wav`（VOICEVOX 音源）

「修正がある場合は教えてください。問題なければ Phase E（素材収集）へ進みます」

---

## Phase E: 素材収集

**目的**: Wikipedia / Wikidata / Wikimedia Commons / Openverse から合法な CC 系ライセンス画像を自動取得し、取得できなかった分だけユーザーに手動配置を依頼し、最後に採用画像を一括でローカル補正する。

### Step E-1: 自動取得（必ず最初に実行）

script.md の登場人物名（3名）を `--names` に渡して自動取得を実行する:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/fetch_materials.py" \
  --materials-dir "[materials/の絶対パス]" \
  --names "人物1,人物2,人物3"
```

または script.md から自動抽出する場合:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/fetch_materials.py" \
  --materials-dir "[materials/の絶対パス]" \
  --script "[script.mdの絶対パス]"
```

- `--candidates-per-person 10` で人物ごとの候補ダウンロード枚数を増やせる
- Wikipedia 記事のメイン画像と Wikidata の P18 を優先取得する
- Wikidata の Commons category / `haswbstatement:P180=Q...` 検索も使って候補を増やす
- 同一人物のスロットでは別名・英語名・検索クエリを変えて重複を回避する
- `materials/[人物名]/metadata.json` に取得元とライセンス情報を保存する
- 取得できなかったスロットのみ「手動配置が必要」として出力される

### Step E-2: 失敗分のみユーザーに手動依頼

スクリプトの出力で **「手動配置が必要なスロット」** に列挙されたファイルだけを提示する:

```
⚠ 手動配置が必要なスロット (N件):
  02_s1_2.jpg  ← 「橋本環奈」の画像を手動で配置してください
  ...
```

提示形式（失敗したスロットのみ）:
```
### [ファイル名] — [用途]
- 推奨イメージ: [具体的な描写]
- 検索キーワード(英語): "[keyword]"
- 推奨サイト: Wikimedia Commons / Openverse / Pexels / Unsplash
```

### Step E-3: 素材確認

ユーザーが「素材を入れました」または「自動取得完了」と伝えたら materials/ フォルダを確認する。不足があれば追加を依頼する。

### Step E-4: 素材が揃った後に一括画質アップ

手動配置も含めて `materials/` の採用画像が揃ったら、**最後に1回だけ** ローカル処理で一括補正する。
この処理は無料・ローカル完結で、OpenCV ベースの拡大 + 軽いコントラスト補正 + シャープ化を行う。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/upscale_materials.py" \
  --materials-dir "[materials/の絶対パス]"
```

- デフォルトでは `materials/` 直下の採用画像スロットだけを処理する
- 未検出スロットがあっても、フォルダ内に存在する採用画像だけを処理する
- ただし、本来使うはずのスロットが欠けている可能性もあるため、実行前に materials/ の中身は確認する
- 元画像は `materials/_upscale_backup/[timestamp]/` に退避される
- 結果は `materials/upscale_report.json` に保存される
- 追加で拡大率を抑えたい/強めたい場合は `--target-long-side` と `--max-scale` を調整する

---

## Phase F: Remotionテンプレート生成（画像スライドショー版）

**目的**: subtitles.json と materials/ の素材を使って `Remotion/my-video` に Composition を追加する。

**重要**: 別途 `remotion/` フォルダは作らない。すべて `Remotion/my-video` に統合する。

```
Remotion/my-video/
├── src/viral/
│   ├── components/         ← 共有コンポーネント（初回のみコピー）
│   └── ViralVideo_[タイトル].tsx  ← 動画ごとに新規生成
└── public/viral/[タイトル]/
    ├── materials/          ← 画像素材
    └── audio/              ← narration.wav + bgm + sfx/
```

### メディアトラック統合ルール（必須）

- 同じ種類で時系列が重ならない素材は、種類ごとに `<Sequence>` を **1本** に統合する。
- `map(...<Sequence>...)` で非重複な同種素材を並べるテンプレートは生成しない。
- 「1本の `<Sequence>` + タイムライン配列 + 現在フレームでアクティブ素材を選ぶ」構造を優先する。
- 複数 `<Sequence>` を出力してよいのは、クロスフェードや同時表示など時間重複が必要な場合だけ。

### Step F-1: 素材一覧を確認・public/viral/ に配置

```bash
MY_VIDEO="/Users/deguchishouma/team-info/Remotion/my-video"
TITLE="[タイトル]"  # 例: 際どいシーン_芸能人_20260311

mkdir -p "$MY_VIDEO/public/viral/$TITLE/materials"
mkdir -p "$MY_VIDEO/public/viral/$TITLE/audio/sfx"

# materials/ の内容をコピー
cp -L "[materials/の絶対パス]"/*.{jpg,png} "$MY_VIDEO/public/viral/$TITLE/materials/"

# audio/ の内容をコピー
cp "[output/タイトル/audio]"/*.wav "$MY_VIDEO/public/viral/$TITLE/audio/"
cp "[output/タイトル/audio/sfx]"/*.wav "$MY_VIDEO/public/viral/$TITLE/audio/sfx/"
```

### Step F-2: 共有コンポーネントの確認（初回のみ）

`Remotion/my-video/src/viral/components/` に以下が存在するか確認する:
- `ImageScene.tsx`, `Hook.tsx`, `Subtitle.tsx`, `ZoomEffect.tsx`, `Scene.tsx`
- `../types.ts`（`src/viral/types.ts`）

存在しない場合のみ `.agent/skills/viral-template-generator/template/src/components/` からコピーする。

### Step F-3: ViralVideo_[タイトル].tsx を生成

**出力先**: `Remotion/my-video/src/viral/ViralVideo_[タイトル].tsx`

`subtitles.json` と素材一覧を読み込み、以下のルールで生成する。

**import パス（必須）:**
```typescript
import { ImageScene } from "./components/ImageScene";
import { Hook } from "./components/Hook";
// PLATFORM_CONFIG は使用しない（未使用変数エラーになるため）
```

**staticFile パス（必須）:**
```typescript
// materials と audio は viral/[タイトル]/ プレフィックスをつける
staticFile("viral/[タイトル]/materials/00_hook.jpg")
staticFile("viral/[タイトル]/audio/narration.wav")
staticFile("viral/[タイトル]/audio/sfx/whoosh.wav")
```

**背景画像トラック（クロスフェード付き・必須）:**

- `SCENE_TIMELINE` 配列を定義（`{ from, to, src, motionType?, motionIntensity?, motionProfile?, originX?, originY? }[]`）
- `FADE_FRAMES = 12`（0.4秒 @ 30fps）でシーン間クロスフェード
- `SceneImage` コンポーネントで1エントリを描画し、`ImageSceneTrack` でフェードを制御する
- 1本の `<Sequence from={0}>` + `ImageSceneTrack` で統合する

```typescript
const FADE_FRAMES = 12;

const SceneImage: React.FC<{ entry: typeof SCENE_TIMELINE[0] }> = ({ entry }) => (
  <ImageScene
    src={entry.src}
    motionType={(entry.motionType as any) ?? "static"}
    motionProfile={entry.motionProfile ?? "still"}
    motionIntensity={entry.motionIntensity ?? 0}
    originX={entry.originX ?? 0.5}
    originY={entry.originY ?? 0.5}
  />
);

const ImageSceneTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const idx = SCENE_TIMELINE.findIndex((s) => frame >= s.from && frame < s.to);
  const current = idx >= 0 ? SCENE_TIMELINE[idx] : SCENE_TIMELINE[SCENE_TIMELINE.length - 1];
  const prev = idx > 0 ? SCENE_TIMELINE[idx - 1] : null;
  const relFrame = idx >= 0 ? frame - current.from : 0;
  const isFading = prev !== null && relFrame < FADE_FRAMES;
  const fadeOpacity = isFading ? relFrame / FADE_FRAMES : 1;
  return (
    <AbsoluteFill>
      {isFading && (
        <AbsoluteFill style={{ opacity: 1 - fadeOpacity }}>
          <SceneImage entry={prev!} />
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ opacity: fadeOpacity }}>
        <SceneImage entry={current} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
```

**motionProfile（必須）:**

| motionProfile | 説明 | 使いどころ |
|---|---|---|
| `"still"` | 完全静止 | 基本（大半のシーン） |
| `"gentle"` | 超低速ズーム/パン | 必要なアクセントシーン |
| `"standard"` | 標準速度 | 参照動画に激しい動きがある場合 |

基本方針: **基本は static+still / 要所だけ zoom_in+gentle / ゆるいパンをたまに** という落ち着いたテンポを保つ。

**カメラワークの再現（必須）:**

`analysis.json` の `video_structure.cuts` に `motion_type` / `motion_intensity` / `origin_x` / `origin_y` が含まれる。
シーンカットのタイミングと SCENE_TIMELINE のフレームを照合し、対応する値を使う。

```typescript
// SCENE_TIMELINE の例（カメラワークつき）
const SCENE_TIMELINE = [
  { from: 0,   to: 90,  src: staticFile("..."), motionType: "zoom_in",   motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
  { from: 90,  to: 270, src: staticFile("..."), motionType: "pan_right",  motionIntensity: 1.2, originX: 0.3, originY: 0.5 },
  { from: 270, to: 390, src: staticFile("..."), motionType: "tilt_up",    motionIntensity: 0.8, originX: 0.5, originY: 0.7 },
  { from: 390, to: 540, src: staticFile("..."), motionType: "zoom_out",   motionIntensity: 1.0, originX: 0.5, originY: 0.4 },
  { from: 540, to: 690, src: staticFile("..."), motionType: "shake",      motionIntensity: 1.5, originX: 0.5, originY: 0.5 },
];

// ImageSceneTrack での使い方
const ImageSceneTrack: React.FC = () => {
  const frame = useCurrentFrame();
  const entry = SCENE_TIMELINE.find((s) => frame >= s.from && frame < s.to)
    ?? SCENE_TIMELINE[SCENE_TIMELINE.length - 1];
  return (
    <AbsoluteFill>
      <ImageScene
        src={entry.src}
        motionType={entry.motionType ?? "zoom_in"}
        motionIntensity={entry.motionIntensity ?? 1.0}
        originX={entry.originX ?? 0.5}
        originY={entry.originY ?? 0.4}
      />
    </AbsoluteFill>
  );
};
```

**利用可能な `motionType` 一覧:**

| motionType | 説明 | 激しさの目安 |
|---|---|---|
| `zoom_in` | ゆるやかなズームイン（Ken Burns） | intensity 0.5–1.0 |
| `zoom_out` | ズームアウト | intensity 0.5–1.0 |
| `pan_right` | 右へスライド | intensity 0.8–1.5 |
| `pan_left` | 左へスライド | intensity 0.8–1.5 |
| `tilt_up` | 上へスライド | intensity 0.8–1.5 |
| `tilt_down` | 下へスライド | intensity 0.8–1.5 |
| `shake` | カメラシェイク（インタラプト演出に） | intensity 1.5–2.0 |
| `static` | 静止 | — |

**字幕スタイル（SUBTITLE_STYLE）:**

`subtitle_style_template.json` が **approved** ならそれを最優先で使う。
未レビューまたは空欄がある場合のみ `analysis.json.subtitle_visual` を補助的に参照する。

ユーザーからローカルフォントの明示指定がある場合は、その指定を優先してよい。
その場合はフォントファイルを `Remotion/my-video/public/assets/fonts/` に配置し、
`FontFace` で明示ロードしてから `fontFamily` に反映する。

- `fontFamily`: `subtitle_style_template.json.subtitle.fontFamily`
- `fontSize`: `subtitle_style_template.json.subtitle.fontSizePx1920h`
- `fontWeight`: `subtitle_style_template.json.subtitle.fontWeight`
- `color`: `subtitle_style_template.json.subtitle.textColor`
- `background`: `subtitle_style_template.json.subtitle.background`
- `paddingH` / `paddingV` / `borderRadius`: 同テンプレ値
- `yPercent`: `subtitle_style_template.json.subtitle.yPercent`
- `strokeWidth` / `strokeColor`: `subtitle_style_template.json.subtitle.strokeWidthPx` / `strokeColor`
- `lineColors`: `subtitle_style_template.json.subtitle.lineColors`
- `textShadow`: レビュー値がなければ `glow_detected=true` のときだけ補完

**禁止事項:**
- `fontFamily` を「どうせ丸ゴだろう」で固定しない
- `fontSize` を `font_size_px=0` なのに独自値で決め打ちしない
- スクショレビュー未実施なのに reference 動画と同じと断定しない

**字幕トラック（行ごと色設定・名前カード対応・必須）:**

- `subtitles.json` の segments を `SUBTITLE_TIMELINE` 配列として定義（`\n` 折り返し済みのテキストをそのまま使う）
- 長い動画では `src/viral/generated/[タイトル]Subtitles.ts` に分離して import してもよい
- 1本の `<Sequence from={0}>` + `SubtitleTrack` コンポーネントで統合
- **冒頭フック期間は必ず `return null`（二重表示防止）**: `SubtitleTrack` 先頭で `if (frame < hookOverlayEndFrames) return null;`
- **行ごとに `<div>` を分けて個別に色を設定する**（`<span>` 1つで完結しない）
- **名前カードルール（必須）**: `/^[1-3]\./.test(text.trim())` で検出し、色を `#FFE400`（鮮黄色）・フォントサイズを170px（通常字幕より大きく）にする
- **名前カードの形式（必須）**: `"1.人物名"` — 「N人目は」形式ではなく `N.名前` 形式で統一する

```typescript
const NAME_COLOR = "#FFE400";
const NAME_COLORS = [NAME_COLOR, NAME_COLOR];

const getLineColors = (text: string, from: number): string[] => {
  const lines = text.split("\n");
  const isNameCard = /^[1-3]\./.test(text.trim());
  if (isNameCard) return lines.map((_, i) => NAME_COLORS[i] ?? "#ffffff");
  if (from < 90) return lines.map((_, i) => HOOK_LINE_COLORS[i] ?? HOOK_LINE_COLORS[0]);
  return lines.map(() => SUBTITLE_STYLE.color);
};

// SubtitleTrack 内の行レンダリング
{lines.map((line, index) => {
  const isNameCard = /^[1-3]\./.test(entry.text.trim());
  return (
    <div
      key={`${entry.from}-${index}-${line}`}
      style={{
        fontSize: isNameCard ? 170 : SUBTITLE_STYLE.fontSize,
        color: lineColors[index] ?? SUBTITLE_STYLE.color,
        whiteSpace: "pre-wrap",
        WebkitTextStroke: `${SUBTITLE_STYLE.strokeWidth} ${SUBTITLE_STYLE.strokeColor}`,
        textShadow: SUBTITLE_STYLE.textShadow,
      }}
    >
      {line}
    </div>
  );
})}
```

**音声トラック:**
```typescript
// BGM（ループ）
<Sequence from={0} durationInFrames={totalFrames}>
  <Audio src={staticFile("viral/[タイトル]/audio/bgm_generated.wav")} volume={0.18} loop />
</Sequence>
// ナレーション
<Sequence from={0} durationInFrames={totalFrames}>
  <Audio src={staticFile("viral/[タイトル]/audio/narration.wav")} volume={1.0} />
</Sequence>
// SFX（セクション境界タイミング）
const SFX_EVENTS = [
  { from: [フレーム数], src: staticFile("viral/[タイトル]/audio/sfx/whoosh.wav"), volume: 0.52 },
  ...
];
```

**フック演出:**
- `<Sequence from={0} durationInFrames={hookOverlayEndFrames}>` + `<Hook>` コンポーネント
- `hookOverlayEndFrames = Math.max(Math.round(3 * fps), SUBTITLE_TIMELINE[0]?.to ?? Math.round(3 * fps))` — 字幕の最初のエントリが3秒以上の場合に合わせて延長する
- Hook の text は SUBTITLE_TIMELINE[0]?.text をそのまま渡す（手動改行を尊重するため自動分割は不要）
- Hook コンポーネントへの必須 props:

```typescript
<Hook
  hookType="statement"
  text={hookText}
  startFrame={hookTextStartFrame}
  endFrame={hookOverlayEndFrames}
  durationFrames={hookOverlayEndFrames}
  fontFamily={SUBTITLE_STYLE.fontFamily}
  fontSize={160}
  strokeWidth={SUBTITLE_STYLE.strokeWidth}
  strokeColor={SUBTITLE_STYLE.strokeColor}
  textShadow={SUBTITLE_STYLE.textShadow}
  lineColors={HOOK_LINE_COLORS}
  paddingTop="65%"
/>
```

- `.replace("\n", " ")` で1行化するのは**禁止**（長い行が変な位置で折り返す）
- 必要な場合のみ `splitHookText` ヘルパーで分割する:
```typescript
const splitHookText = (raw: string): string => {
  const MAX = 11;
  return raw.replace(/\n+/g, "\n").split("\n")
    .flatMap((line) => {
      if (line.length <= MAX) return [line];
      const mid = Math.round(line.length / 2);
      return [line.slice(0, mid), line.slice(mid)];
    }).join("\n");
};
// 使い方: text={splitHookText(SUBTITLE_TIMELINE[0]?.text ?? "")}
```
- `hookDurationFrames = Math.round(3 * fps)` を `ViralVideo` コンポーネント内で定義し、`SubtitleTrack` でも同じ値を使って冒頭スキップする（`Math.round(3 * fps)` と直書きしてよい）

**フック行色の自動割り当て（必須）:**

`splitHookText` で改行位置を確定した後、行数に応じて以下の順で色を割り当てる:

| 行インデックス | 色 | カラーコード |
|---|---|---|
| 0（1行目） | 黄 | `#f4d56f` |
| 1（2行目） | サーモン | `#f4a898` |
| 2（3行目） | ライトピンク | `#f0c8d8` |
| 3以降 | 白 | `#ffffff` |

```typescript
// 参考動画5本（狙ってた芸能人3選・女優魂・食べちまった・バナナ・アスリート）から抽出した定番配色
const HOOK_LINE_COLORS = ["#f4d56f", "#f4a898", "#f0c8d8", "#ffffff"];
// 行数が4を超える場合は末尾を #ffffff で埋める
// lineColors={HOOK_LINE_COLORS} を Hook コンポーネントに渡す
```

行数が増えても `HOOK_LINE_COLORS[index] ?? "#ffffff"` で対応できるため、配列は4要素で固定してよい。
チャンネルが `adult_affiliate_retro` テンプレート使用時は必ずこの配色を使う。

**パターンインタラプト:**
- `INTERRUPT_FRAMES` 配列を定義
- 1本の `<Sequence from={0}>` + `FlashTrack` コンポーネントで統合

**durationInFrames:** `Math.ceil(total_duration_seconds * fps)`

### Step F-4: Root.tsx に Composition を追加

**出力先**: `Remotion/my-video/src/Root.tsx`

**命名ルール**:
- コンポジション source は `Remotion/my-video/src/viral/[テンプレ名]/[テーマ]_[yyyyMMdd].tsx` に置く
- `Root.tsx` では `Folder` を使って `Viral相当 / テンプレ名 / テーマごとのComposition` の階層にする
- このリポジトリでは `Remotion/my-video/scripts/patch_remotion_japanese_support.mjs` により、`Folder name` と `Composition id` でも日本語を使える前提で運用する
- **Composition の `id` は必ず日本語（タイトル＋日付）にする**。英語・ローマ字は使わない。
  - 使用可能文字: `a-z`, `A-Z`, `0-9`, 日本語, `-`（ハイフン）のみ。`_`（アンダースコア）は**使用不可**。
  - 例: `id="ガチで脱いだ女性芸能人3選-20260313"` ← OK（ハイフン区切り）
  - 例: `id="ガチで脱いだ女性芸能人3選_20260313"` ← NG（アンダースコア不可）
  - 例: `id="gachi-nuida-20260313"` ← NG（英語不可）

```typescript
// import に追加
import { ViralVideo } from "./viral/[テンプレ名]/[タイトル]";

// RemotionRoot 内に追加
<Folder name="Viral">
  <Folder name="[テンプレ名]">
    <Composition
      id="[テーマ]-[yyyyMMdd]"
      component={ViralVideo}
      durationInFrames={[total_frames]}
      fps={30}
      width={1080}
      height={1920}
    />
  </Folder>
</Folder>
```

### Step F-5: lint 確認

```bash
node /Users/deguchishouma/team-info/Remotion/my-video/node_modules/typescript/bin/tsc \
  --noEmit --project /Users/deguchishouma/team-info/Remotion/my-video/tsconfig.json
```

### Step F-6: サムネ用スクショ生成（必須）

**目的**: フック字幕が画面に出ているタイミングで1フレームをレンダリングし、サムネイル候補として保存する。

**フレームの決め方**: `SUBTITLE_TIMELINE[0]` の中間フレームを使う。
- 計算式: `Math.round((from + to) / 2)`
- 例: フック `{ from: 0, to: 82 }` → フレーム 41

**保存先**: `outputs/viral/サムネ/[タイトル]/hook_frame[N].png`

```bash
COMP_ID="[Composition id（日本語・ハイフン区切り）]"
TITLE="[タイトル（アンダースコア区切り）]"
FRAME=[SUBTITLE_TIMELINE[0].from と .to の中間値]

cd /Users/deguchishouma/team-info/Remotion/my-video && \
  /Users/deguchishouma/.nvm/versions/node/v22.17.1/bin/npx remotion still \
  "$COMP_ID" \
  "/Users/deguchishouma/team-info/outputs/viral/サムネ/$TITLE/hook_frame${FRAME}.png" \
  --frame=$FRAME
```

- 複数フレームを確認したい場合は `--frame` の値を変えて追加生成してよい
- フック字幕が出るタイミングを狙うため、`from` より少し後（+5〜10f）で取るとアニメーションが落ち着いた状態になる

### Step F-7: ユーザーへの報告

以下を報告する:
- 生成ファイル一覧
- 字幕セグメント数・フック情報・素材数
- サムネ保存先パス

次に **Phase G（ジェットカット）** を実行する。

---

## Phase G: ジェットカット（無音短縮）

**目的**: narration.wav の無音期間を librosa で検出し、セグメント間の長い無音を食い気味（約 0.08s）に短縮する。
音声・字幕・画像シーン・SFX の全タイムラインを連動して更新する。

### Step G-1: ジェットカット実行

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/.agent/skills/viral-template-generator/scripts/jet_cut.py" \
  --audio  "$TEAM_INFO_ROOT/Remotion/my-video/public/viral/[タイトル]/audio/narration.wav" \
  --tsx    "$TEAM_INFO_ROOT/Remotion/my-video/src/viral/ViralVideo_[タイトル].tsx" \
  [--min-silence 0.20] \
  [--keep-silence 0.08] \
  [--top-db 40]
```

**パラメータ説明:**

| オプション | デフォルト | 説明 |
|---|---|---|
| `--min-silence` | `0.20` | これ以上の無音 gap を切る（秒） |
| `--keep-silence` | `0.08` | 切後に残す無音。小さいほど食い気味（秒） |
| `--top-db` | `40` | 無音判定の dB 閾値。大きいほど厳しく検出 |
| `--dry-run` | — | ファイルを変更せず切りどころだけ確認 |

**まず `--dry-run` で確認してから本番実行することを推奨。**

### Step G-2: 更新されるファイル

スクリプトが自動的に以下を更新する（元ファイルは `.before_jetcut.*` でバックアップ）:

| ファイル | 更新内容 |
|---|---|
| `narration_jetcut.wav` | 無音短縮済み音声（新規生成） |
| `generated/[xxx]Subtitles.ts` | `SUBTITLE_TIMELINE` の from/to フレーム番号を再計算 |
| `ViralVideo_[タイトル].tsx` | `SCENE_TIMELINE` / `INTERRUPT_FRAMES` / `SFX_EVENTS.from` / `totalFrames` / audio src を再計算 |
| `Remotion/my-video/src/Root.tsx` | 対象 Composition の `durationInFrames` を最新尺へ同期 |

### Step G-3: lint 確認 & プレビュー

```bash
node /Users/deguchishouma/team-info/Remotion/my-video/node_modules/typescript/bin/tsc \
  --noEmit --project /Users/deguchishouma/team-info/Remotion/my-video/tsconfig.json
```

問題なければプレビュー:
```bash
npm --prefix /Users/deguchishouma/team-info/Remotion/my-video run dev
```

---

## Phase H: レンダリング

```bash
npm --prefix /Users/deguchishouma/team-info/Remotion/my-video run render -- \
  --composition=Viral-[platform]-[yyyyMMdd] \
  --output="/Users/deguchishouma/team-info/outputs/viral/[タイトル].mp4"
```

---

## プラットフォーム設計方針

```typescript
const PLATFORM_CONFIG = {
  tiktok:  { width: 1080, height: 1920, maxDuration: 60,  subtitleFontSize: 52, subtitleY: 75 },
  shorts:  { width: 1080, height: 1920, maxDuration: 60,  subtitleFontSize: 48, subtitleY: 72 },
  reels:   { width: 1080, height: 1920, maxDuration: 90,  subtitleFontSize: 44, subtitleY: 70 },
}
```
