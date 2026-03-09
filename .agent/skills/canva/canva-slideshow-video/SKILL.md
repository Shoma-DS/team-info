---
name: canva-slideshow-video
description: 台本からCanvaでスライドを生成し、音源と同期したスライドショー動画を制作するスキル
---

# Canva スライドショー動画制作スキル

台本 → Canvaスライド生成 → PNG エクスポート → 音源化 → Remotion で動画化

---

## 前提条件

- `~/.secrets/canva_tokens.json` にアクセストークンが保存済み
  - 未取得の場合: `python3 $TEAM_INFO_ROOT/mcp-servers/canva_auth.py` を実行
- VOICEVOX エンジンが起動済み（音源化ステップで必要）

---

## 制作フロー

### Step 1: 台本を確認・選択

- 台本: `Remotion/scripts/voice_scripts/` 内の `.md` ファイル
- かな版（`_kana.md`）がない場合は先に作成する（読み間違い防止）

### Step 2: Canva スライド生成

```bash
python3 $TEAM_INFO_ROOT/mcp-servers/canva_slideshow.py \
  --script "台本ファイル名.md" \
  --theme "テーマ名"
```

- 台本を段落単位で分割し、Canva Connect API でプレゼンテーションを自動生成
- 生成後、CanvaのURLが表示される → ブラウザでデザインを確認・編集してから Enter
- PNG としてエクスポートし `outputs/canva_slides/{テーマ}/` に保存
- `manifest.json` にスライドテキストと画像パスの対応を記録

### Step 3: 音源化

```bash
python3 $TEAM_INFO_ROOT/Remotion/generate_voice.py
```

- かな版台本（`_kana.md`）が存在すればそちらを自動使用
- 出力先: `outputs/sleep_travel/audio/{日付}_{テーマ}.mp3`

### Step 4: Remotion で動画化

`Root.tsx` に以下を追加（音声の実際のフレーム数に合わせる）：

```tsx
import { CanvaSlideshow } from "./CanvaSlideshow";
import slidesData from "../public/assets/canva_slides/{テーマ}/manifest.json";

<Composition
  id="CanvaSlideshow-{テーマ}"
  component={CanvaSlideshow}
  durationInFrames={/* 音声秒数 × 30 */}
  fps={30}
  width={1920}
  height={1080}
  defaultProps={{
    audioSrc: "outputs/sleep_travel/audio/{日付}_{テーマ}.mp3",
    manifestSrc: "assets/canva_slides/{テーマ}/manifest.json",
    slides: slidesData,
  }}
/>
```

レンダリングコマンド（出力しますか？を確認してから実行）:

```bash
cd $TEAM_INFO_ROOT/Remotion/my-video && npx remotion render src/index.ts \
  CanvaSlideshow-{テーマ} \
  --output="$TEAM_INFO_ROOT/outputs/canva_slides/{テーマ}/{テーマ}.mp4"
```

---

## ファイル構成

```
team-info/
├── mcp-servers/
│   ├── canva_auth.py          # OAuthトークン取得
│   └── canva_slideshow.py     # スライド生成・エクスポート
├── Remotion/
│   ├── generate_voice.py      # 音源化
│   └── my-video/src/
│       └── CanvaSlideshow.tsx # Remotion コンポーネント
└── outputs/
    └── canva_slides/{テーマ}/
        ├── slide_001.png
        ├── slide_002.png
        ├── ...
        ├── manifest.json      # スライド←→テキスト対応
        └── {テーマ}.mp4       # 最終動画
```

---

## 注意事項

- Canva アクセストークンの有効期限は4時間。期限切れ時は自動リフレッシュ
- スライドの文字数は1枚あたり最大120文字（`MAX_CHARS_PER_SLIDE`で調整可）
- スライド切り替えタイミングは音声の長さを均等分割（将来的にWhisperで精密化可能）
- Canvaでデザインを手動編集してからエクスポートすることを推奨
- レンダリング前に必ず「出力しますか？書き出しますか？」の確認をとること
