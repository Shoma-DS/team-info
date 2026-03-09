---
name: canva-slideshow-video
description: 台本に合った背景画像でスライドを生成し、音源と同期したスライドショー動画を制作するスキル（Remotion直接描画方式）
---

# スライドショー動画制作スキル

台本 → 音声プロファイル選択 → 台本選択 → 背景画像生成（Pixabay）→ 音源化 → Remotion で動画化

---

## 前提条件

- VOICEVOX エンジンが起動済み
- `~/.secrets/pixabay_api_key.txt` に Pixabay API キーが保存済み
  - 未取得: https://pixabay.com/api/docs/ で無料登録（従量課金なし）
  - 初回のみ `--save-key` オプションで保存: `python3 mcp-servers/generate_slides.py ... --pixabay-key KEY --save-key`

---

## 制作フロー

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
python3 $TEAM_INFO_ROOT/mcp-servers/generate_slides.py \
  --script "台本ファイル名.md" \
  --theme "テーマ名" \
  --max-slides 20
```

- 台本の各段落からキーワード抽出 → Pixabay で台本に合った背景画像を取得
- 画像は `Remotion/my-video/public/assets/slide_images/{テーマ}/images/` に保存
- `manifest.json`（テキスト + 画像パス対応）を生成

### Step 4: 音源化

Step 1 で選んだプロファイルを `--profile` に指定して実行:

```bash
python3 $TEAM_INFO_ROOT/Remotion/generate_voice.py \
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
    ├── manifest.json           # スライド←→テキスト+画像パス対応
    └── audio.mp3               # 音源（コピー済み）
```

---

## 注意事項

- **フロー順序厳守: 音声選択 → 台本選択 → 実行**（ユーザーに提示してから進む）
- スライド数は `--max-slides` で調整（デフォルト20枚推奨、長尺は30〜40枚まで）
- 画像取得に失敗したスライドはグラデーション背景で自動フォールバック
- BGM を追加する場合は `bgmSrc` prop を指定（`assets/channels/sleep_travel/bgm/焚き火ループ.mp3` など）
- レンダリング出力先は必ず `outputs/sleep_travel/renders/` を使う
