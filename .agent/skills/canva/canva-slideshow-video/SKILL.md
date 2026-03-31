---
name: canva-slideshow-video
description: 台本に合った背景画像でスライドを生成し、音源と同期したスライドショー動画を制作するスキル（Remotion直接描画方式）
---

# スライドショー動画制作スキル

---

## ★ スキル起動時に必ずやること（順番厳守）

### 0. フロー全体をユーザーに説明する

スキル起動直後、以下の内容をユーザーに提示する:

```
【スライドショー動画制作フロー】

Step 1: 音声プロファイルを選択
Step 2: 台本を選択
Step 3: 素材フォルダの確認（台本ファイルが入っているか）
Step 4: 背景画像を自動生成（Pixabay）
Step 5: 音源化（VOICEVOX）
Step 6: Remotion で動画レンダリング

所要時間目安: 背景画像取得 約1〜3分 / 音源化 テキスト量による / レンダリング 数分〜数時間
```

### 0-b. 素材フォルダを走査してユーザーに確認する

以下のフォルダをスキャンし、実在するファイルを番号付きで提示する:

**台本フォルダ**: `Remotion/scripts/voice_scripts/`
- `.md` と `.txt` を対象に走査
- ファイルがない場合は「台本ファイルが見つかりません。先に台本を作成してください」と報告

提示例:
```
【台本フォルダ: Remotion/scripts/voice_scripts/】
1. 地政学_世界を動かす地理の読み方_20260211.md
2. 北欧神話_氷と炎の世界_20260115.md
...

台本ファイルは上記の通りです。素材の準備はできていますか？
準備OKなら「はい」と答えてください。
```

**ユーザーが「はい」と答えるまで次のStepに進まない。**

---

## 前提条件

- VOICEVOX Engine が起動済み
  - 状態確認: `python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" voicevox-engine-status`
  - 起動: `python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" start-voicevox-engine`
- `~/.secrets/pixabay_api_key.txt` に Pixabay API キーが保存済み
  - 未取得: https://pixabay.com/api/docs/ で無料登録（従量課金なし）
  - 初回のみ `--save-key` オプションで保存: `python "$TEAM_INFO_ROOT/mcp-servers/generate_slides.py" ... --pixabay-key KEY --save-key`

---

## 制作フロー

### Remotion実装ルール（必須）

- 画像スライド、差し替えBGM、補助効果音など、同じ種類で時系列が重ならない素材は、種類ごとに `<Sequence>` を1本へ統合する。
- `CanvaSlideshow.tsx` では `slides.map(...<Sequence>...)` のように画像スライドごとに `<Sequence>` を量産しない。
- スライドは「画像用 `<Sequence>` 1本 + タイムライン配列 + 現在フレームからアクティブな1枚を選択して描画」を標準実装にする。
- 音声も複数クリップが非重複なら同様に1トラック化を優先し、BGMループだけは `<Loop>` で管理してよい。
- 複数 `<Sequence>` を分けるのは、クロスフェードなど同種素材の時間重複が必要な場合だけに限定する。
- 生成・更新する **すべての `<Sequence>` に `name` を付ける。** 例: `画像スライド`, `BGM`, `効果音`, `字幕`, `音声 ナレーション`。

### 記事反映で追加した構成原則

- 冒頭 1 から 2 枚は「説明」より「フック」を優先する。要約を先に全部出さず、違和感・問い・強い一文で続きを見たくさせる。
- 1枚に 1メッセージを徹底する。長文をそのまま焼き込まず、`headline` と `body` に圧縮して見出しの強弱を出す。
- 数字、事例、引用、人物感がある話題は通常スライドに埋もれさせず、中盤に `具体例` スライドとして差し込む。
- 人物紹介や発信者の文脈がある段落は `人物` スライドとして扱い、顔写真・プロフィール画像・記事スクショなどの手持ち素材がある場合は Pixabay より優先して使う。
- 話題転換は無理に本文へ混ぜず、短い `切り替え` スライドを挟んでテンポを作る。
- 背景画像検索は段落全文ではなく、圧縮後の見出し・補足文を優先して行い、画とメッセージのズレを減らす。
- スライド表示時間は均等割りではなく、テキスト量に応じて重み付けして、短い要点と長い説明の滞在時間を分ける。

### Step 1: 音声プロファイルを選択（必須・最初に確認）

`Remotion/configs/voice_config.json` に登録済みのプロファイル一覧をユーザーに提示し、
**どの声を使うか先に確定**してから次に進む。

| プロファイル名 | 声 | 特徴 |
|---|---|---|
| `aoyama_ryuusei_normal` | **青山龍星**（基本の声） | 落ち着いた男性ナレーター |
| `narrator_male` | 雨晴はう | 穏やかな男性 |
| `narrator_female` | 四国めたん | 落ち着いた女性 |
| `shikoku_metan_whisper` | 四国めたん（ささやき） | 囁き系・睡眠向き |
| `default` / `zundamon_normal` | ずんだもん | 明るい女性 |

### Step 2: 台本を選択

- 台本: `Remotion/scripts/voice_scripts/` 内の `.md` ファイルを走査して番号付きで提示
- かな版（`_kana.md`）がない場合は先に作成する（読み間違い防止）

### Step 3: 背景画像生成（Pixabay）

```bash
python "$TEAM_INFO_ROOT/mcp-servers/generate_slides.py" \
  --script "台本ファイル名.md" \
  --theme "テーマ名" \
  --max-slides 20
```

- 台本の各段落からキーワード抽出 → Pixabay で台本に合った背景画像を取得
- 画像は `Remotion/my-video/public/assets/slide_images/{テーマ}/images/` に保存
- `manifest.json` は `text` に加えて `headline` / `body` / `layout` / `label` / `highlight` も持つ構造で生成し、Remotion 側でフック・要点・具体例・人物感の見せ方を変えられるようにする

### Step 4: 音源化

Step 1 で選んだプロファイルを `--profile` に指定して実行:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "$TEAM_INFO_ROOT/Remotion/generate_voice.py" \
  --script "台本ファイル名.md" \
  --profile "aoyama_ryuusei_normal" \
  --theme "テーマ名"
```

- かな版台本（`_kana.md`）が存在すれば自動使用、音源化後に自動削除
- 出力先: `outputs/sleep_travel/audio/{日付}_{テーマ}.mp3`
- 音源の秒数を `ffprobe` で確認 → `durationInFrames = 秒数 × 30`

### Step 5: Remotion で動画化

音源を `Remotion/my-video/public/assets/slide_images/{テーマ}/audio.mp3` にコピー後、
`Root.tsx` に以下を追加:

```tsx
import { CanvaSlideshow } from "./CanvaSlideshow";
import slidesData from "../public/assets/slide_images/{テーマ}/manifest.json";

<Composition
  id="SleepTravel-{テーマ}-Slideshow"
  component={CanvaSlideshow}
  durationInFrames={/* 音声秒数 × 30 */}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{
    audioSrc: 'assets/slide_images/{テーマ}/audio.mp3',
    slides: slidesData,
  }}
/>
```

- `CanvaSlideshow.tsx` の画像トラックは `<Sequence>` 1本で管理し、現在フレームに応じて表示するスライドを切り替える。
- スライドごとに sibling の `<Sequence>` を増やしてタイムラインを分断しない。
- `manifest.json` に `headline` / `body` / `layout` / `highlight` がある前提で、冒頭フック・切り替え・要点・具体例・人物感のレイアウト差を活かす。
- 旧 manifest の `text` だけでも再生できる後方互換を残しつつ、新規生成分では構造化 manifest を標準にする。

lint チェック後、レンダリング（**必ず「出力しますか？書き出しますか？」を確認してから実行**）:

```bash
cd $TEAM_INFO_ROOT/Remotion/my-video && npx remotion render src/index.ts \
  SleepTravel-{テーマ}-Slideshow \
  --output="$TEAM_INFO_ROOT/outputs/sleep_travel/renders/{テーマ}_slideshow.mp4"
```

---

## ファイル構成

```
team-info/
├── mcp-servers/
│   ├── canva_auth.py           # Canva OAuthトークン取得（Canva方式を使う場合）
│   ├── canva_slideshow.py      # Canva API経由スライド生成（参考用）
│   └── generate_slides.py      # Pixabay背景画像取得・manifest生成（推奨）
├── Remotion/
│   ├── generate_voice.py       # 音源化（VOICEVOX）
│   ├── configs/voice_config.json  # 音声プロファイル定義
│   └── my-video/src/
│       └── CanvaSlideshow.tsx  # Remotion スライドショーコンポーネント
└── Remotion/my-video/public/assets/slide_images/{テーマ}/
    ├── images/slide_001.jpg〜  # Pixabay背景画像
    ├── manifest.json           # `text` + `headline` / `body` / `layout` / `highlight` / 画像パス対応
    └── audio.mp3               # 音源（コピー済み）
```

---

## 注意事項

- **フロー順序厳守: 音声選択 → 台本選択 → 実行**（ユーザーに提示してから進む）
- スライド数は `--max-slides` で調整（デフォルト20枚推奨、長尺は30〜40枚まで）
- 画像取得に失敗したスライドはグラデーション背景で自動フォールバック
- 1枚目は単なる挨拶で終わらせず、その回の違和感・問い・結論の断片を優先してフック化する
- 事例・数字・比較が出る段落は、`具体例` レイアウトとして独立させる前提で台本を書くと見やすい
- BGM を追加する場合は `bgmSrc` prop を指定（`assets/channels/sleep_travel/bgm/焚き火ループ.mp3` など）
- レンダリング出力先は必ず `outputs/sleep_travel/renders/` を使う
