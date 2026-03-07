---
name: viral-template-generator
description: ショート動画を3層解析し、Remotionバズ動画テンプレートを自動生成するスキル。
---

# viral-template-generator スキル

## 概要

入力動画を以下の3層で解析し、Remotion動画テンプレートを自動生成する。

```
input.mp4
 → Layer1: 動画構造解析（カット・顔・テロップ・カメラ）
 → Layer2: 音声解析（Whisper書き起こし・話速・感情）
 → Layer3: バズ構造解析（フック・パターンインタラプト・ループ）
 → analysis.json
 → Claude → Remotionテンプレート
```

## トリガー条件

ユーザーが以下のいずれかを言った場合に起動する:
- `analyze-video [ファイルパス]`
- 「動画を解析してテンプレを作って」
- 「バズテンプレを生成して」

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
│       ├── video_structure.py   # Layer 1
│       ├── speech_analysis.py   # Layer 2
│       └── viral_pattern.py     # Layer 3
└── template/                 # Remotionベーステンプレート
    ├── package.json
    ├── tsconfig.json
    ├── remotion.config.ts
    └── src/
        ├── index.ts
        ├── Root.tsx
        ├── ViralVideo.tsx
        ├── types.ts
        └── components/
            ├── Scene.tsx
            ├── Subtitle.tsx
            ├── ZoomEffect.tsx
            └── Hook.tsx
```

## フェーズ 1: 動画解析（Python）

### セットアップについて（自動処理・Claude は何もしなくてよい）

セットアップは `analyze_video.py` 起動時に自動判定・自動実行される。

- 判定フラグ:
  - macOS / Linux: `~/.config/viral-template-generator/.setup_done`
  - Windows: `%APPDATA%/viral-template-generator/.setup_done`
- フラグが存在しない場合 → `setup.py` を自動実行し、完了後にフラグを書き込む
- フラグが存在する場合 → セットアップをスキップして解析を開始する

Claude はセットアップコマンドをユーザーに提示しなくてよい。

### インボックスフォルダ

解析したい動画は事前に以下のフォルダに置いておく:

```
inputs/viral-analysis/
```

引数なしで起動すると、フォルダ内の動画一覧が表示されインタラクティブに選択できる。

### クロスプラットフォーム通知

選択を促す際・解析完了時に OS ネイティブ通知が送られる（他作業中でも気づける）:

| OS      | 通知方式                                   |
|---------|--------------------------------------------|
| macOS   | `osascript` 通知センター + サウンド        |
| Linux   | `notify-send`（libnotify）+ ターミナルベル |
| Windows | PowerShell タスクトレイ BalloonTip + beep  |

### Step 1-1: 解析実行

以下のコマンドをユーザーに提示し、任意のターミナルから実行するよう案内する:

```bash
python .agent/skills/common/scripts/team_info_runtime.py run-remotion-python -- \
  .agent/skills/viral-template-generator/scripts/analyze_video.py \
  "[入力動画のパス]" \
  --output-dir "[出力先]" \
  --platform [tiktok|shorts|reels]
```

- 完了したら「終わりました」と伝えるよう案内する
- 完了後、出力ディレクトリの `analysis.json` を確認する

## フェーズ 2: Remotionテンプレート生成（Claude）

`analysis.json` を読み込み、以下の手順でテンプレートを生成する。

### Step 2-1: analysis.json を読む

`analysis.json` を Read ツールで読み込み、以下を把握する:
- `platform`: 対象プラットフォーム（TikTok / Shorts / Reels）
- `duration`: 動画の長さ（秒）
- `fps`: フレームレート
- `video_structure.cuts`: シーンカット一覧
- `speech_structure.transcript`: 字幕テキストと時刻
- `viral_structure`: フック・パターンインタラプト・ループ構造

### Step 2-2: テンプレートディレクトリを出力先にコピー

- `.agent/skills/viral-template-generator/template` を `[出力先]/remotion` にコピーする。
- OS依存の `cp -r` は前提にせず、Codex のファイル操作か Python の `shutil.copytree(..., dirs_exist_ok=True)` を使う。

### Step 2-3: ViralVideo.tsx を生成

`analysis.json` の内容に基づき、`[出力先]/remotion/src/ViralVideo.tsx` を以下のルールで生成する:

**durationInFrames の計算:**
```
durationInFrames = Math.ceil(duration * fps)
```

**シーン生成ルール:**
- `video_structure.cuts` の各エントリを1シーンとして `<Scene>` コンポーネントに変換する
- 各シーンの `from` / `durationInFrames` はカット情報から計算する

**字幕生成ルール:**
- `speech_structure.transcript` の各エントリを `<Subtitle>` コンポーネントに変換する
- `start` (秒) を `frame = Math.round(start * fps)` に変換する

**フック演出ルール:**
- `viral_structure.hook_time` から `hook_type` に応じて `<Hook>` コンポーネントを配置する
  - `question`: テキストクイズ演出
  - `statement`: 太字テキスト強調
  - `visual`: ズームイン演出

**ズーム演出ルール:**
- `video_structure.camera_motion` に `zoom` 型があれば `<ZoomEffect>` を配置する

**パターンインタラプト:**
- `viral_structure.pattern_interrupts` の各時刻にフラッシュ・揺れエフェクトを追加する

**プラットフォーム別設定:**
| platform | width | height | fontStyle |
|---|---|---|---|
| tiktok | 1080 | 1920 | bold・大文字 |
| shorts | 1080 | 1920 | clean・ナチュラル |
| reels | 1080 | 1920 | aesthetic・細字 |

### Step 2-4: Root.tsx を更新

生成した Composition を Root.tsx に登録する。

Composition ID の命名規則: `Viral-[プラットフォーム]-[yyyyMMdd]`

### Step 2-5: lint 確認

```bash
cd "[出力先]/remotion" && npx tsc --noEmit
```

### Step 2-6: ユーザーへの報告

以下を報告する:
- 生成ファイル一覧
- 検出されたカット数・字幕数・フック情報
- プレビューコマンド（絶対パス）:
  ```bash
  cd "[出力先]/remotion" && npx remotion studio
  ```
- レンダリングコマンド:
  ```bash
  cd "[出力先]/remotion" && npx remotion render --composition=Viral-[platform]-[date] --output="[出力先]/output.mp4"
  ```

## プラットフォーム設計方針

将来拡張を考慮し、`analysis.json` に `platform` フィールドを持たせる。
各プラットフォームのテンプレート差異は `ViralVideo.tsx` 内の `PLATFORM_CONFIG` で管理する。

```typescript
const PLATFORM_CONFIG = {
  tiktok:  { width: 1080, height: 1920, maxDuration: 60  },
  shorts:  { width: 1080, height: 1920, maxDuration: 60  },
  reels:   { width: 1080, height: 1920, maxDuration: 90  },
}
```
