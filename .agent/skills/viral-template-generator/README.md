# viral-template-generator

ショート動画を3層解析して、Remotionバズ動画テンプレートを自動生成するツール。

## アーキテクチャ

```
input.mp4
  ↓
[Layer 1] 動画構造解析    カット / 顔 / テロップ / カメラ動き
  ↓
[Layer 2] 音声解析         Whisper書き起こし / 話速 / キーワード
  ↓
[Layer 3] バズ構造解析     フック / パターンインタラプト / ループ
  ↓
analysis.json
  ↓
Claude Code → Remotionテンプレート生成
```

## ディレクトリ構造

```
.agent/skills/viral-template-generator/
├── SKILL.md                       # Claude スキル定義
├── README.md                      # このファイル
├── scripts/
│   ├── setup.py                   # 初回セットアップ本体
│   ├── setup.sh                   # POSIX ラッパー
│   ├── analyze_video.py           # メインCLI
│   └── layers/
│       ├── video_structure.py     # Layer 1
│       ├── speech_analysis.py     # Layer 2
│       └── viral_pattern.py       # Layer 3
└── template/                      # Remotionベーステンプレート
    ├── package.json
    ├── tsconfig.json
    ├── remotion.config.ts
    └── src/
        ├── index.ts
        ├── Root.tsx
        ├── ViralVideo.tsx         # メインコンポーネント（Claude が生成）
        ├── types.ts               # 型定義
        └── components/
            ├── Scene.tsx          # シーン（カットベース）
            ├── Subtitle.tsx       # 字幕オーバーレイ
            ├── ZoomEffect.tsx     # ズームアニメーション
            └── Hook.tsx           # フック演出（最初の3秒）
```

## 使い方

### Step 1: セットアップ（初回のみ）

```bash
python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- \
  .agent/skills/viral-template-generator/scripts/setup.py
```

インストールされるもの:
- `opencv-python-headless` — 動画フレーム解析
- `mediapipe` — 顔検出
- `pytesseract` — OCR（テロップ検出）
- `faster-whisper` — 音声書き起こし
- `ffmpeg` — 音声抽出（システム依存、未導入時は案内を表示）
- `tesseract` — OCRエンジン（システム依存、未導入時は案内を表示）

### Step 2: 動画解析

```bash
python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- \
  .agent/skills/viral-template-generator/scripts/analyze_video.py \
  /path/to/input.mp4 \
  --output-dir /path/to/output \
  --platform tiktok
```

オプション:
| オプション | デフォルト | 説明 |
|---|---|---|
| `--platform` | `tiktok` | `tiktok` / `shorts` / `reels` |
| `--output-dir` | `./analysis-output` | analysis.json の出力先 |
| `--skip-ocr` | false | OCRをスキップ（高速化） |

### Step 3: Remotionテンプレート生成

Claude Code に以下を伝える:

```
/path/to/output/analysis.json からRemotionテンプレートを生成して
```

Claude が `analysis.json` を読み、`/path/to/output/remotion/` にカスタマイズされたテンプレートを生成する。

### Step 4: プレビュー・レンダリング

```bash
# プレビュー
cd /path/to/output/remotion && npx remotion studio

# レンダリング
cd /path/to/output/remotion && npx remotion render \
  --composition=Viral-tiktok-20260308 \
  --output=/path/to/output/output.mp4
```

---

## analysis.json の仕様

```jsonc
{
  "duration": 15.2,          // 動画の長さ（秒）
  "fps": 30,
  "platform": "tiktok",      // tiktok / shorts / reels
  "resolution": { "width": 1080, "height": 1920 },

  "video_structure": {
    "cuts": [
      { "start": 0, "end": 1.2, "start_frame": 0, "end_frame": 36 },
      // ...
    ],
    "faces": [
      { "frame": 15, "time": 0.5, "x": 0.5, "y": 0.35, "size": 0.12, "confidence": 0.98 }
    ],
    "text_regions": [
      { "frame": 30, "time": 1.0, "x": 0.5, "y": 0.8, "text": "テロップ", "confidence": 85 }
    ],
    "camera_motion": [
      { "type": "zoom", "start": 3.2, "end": 5.0 }
    ],
    "important_frames": [0, 36, 90]
  },

  "speech_structure": {
    "transcript": [
      { "start": 0.2, "end": 2.5, "text": "今日は○○について話します" }
    ],
    "full_text": "今日は...",
    "words_per_minute": 250,
    "keywords": ["方法", "コツ", "簡単"],
    "emotional_intensity": "high",
    "pauses": [{ "start": 2.5, "end": 3.1, "duration": 0.6 }]
  },

  "viral_structure": {
    "hook_time": 0.2,
    "hook_type": "question",            // question / statement / visual / unknown
    "pattern_interrupts": [3.2, 7.8],
    "loop_point": 14.5,
    "information_density": "high",      // low / medium / high
    "tone": "educational"               // educational / entertainment / curiosity / general
  }
}
```

---

## プラットフォーム設計

| Platform | 解像度 | 最大尺 | 字幕サイズ | スタイル |
|---|---|---|---|---|
| TikTok | 1080×1920 | 60s | 52px | Bold・大文字 |
| YouTube Shorts | 1080×1920 | 60s | 48px | Clean・ナチュラル |
| Instagram Reels | 1080×1920 | 90s | 44px | Aesthetic・細字 |

将来対応予定: `--platform youtube`（横長）

---

## トラブルシューティング

**`mediapipe` インポートエラー**
```bash
python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- -m pip install mediapipe
```

**OCR が動かない**
macOS: `brew install tesseract tesseract-lang`  
Linux: `sudo apt-get install -y tesseract-ocr tesseract-ocr-jpn`  
Windows: `winget install UB-Mannheim.TesseractOCR`

または `--skip-ocr` フラグを使う。

**faster-whisper が遅い**
`base` → `small` → `large-v3` でモデルサイズを変更。
`speech_analysis.py` の `WhisperModel("base", ...)` を変更する。
