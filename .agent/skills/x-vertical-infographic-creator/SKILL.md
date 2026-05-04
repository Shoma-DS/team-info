---
name: x-vertical-infographic-creator
description: >
  X (Twitter) 投稿用の縦型図解・インフォグラフィック画像を設計・プロンプト化するスキル。
  x-post-writer の scheduled_draft_pipeline.py と統合して動作し、
  アカウントごとのキャラクター・デザインルールを accounts/ フォルダで管理する。
  投稿文・ツリー・メモ・コンセプトを入力として受け取り、Xでスクロールを止める
  "強い1枚" の図解コンセプト・レイアウト案・画像生成プロンプト・改善プロンプトを出力する。
  キーワード: X infographic, vertical social post, Japanese diagram, AI workflow,
  Claude Code, Codex, Remotion, image generation prompt, blue clean design, character-based infographic
version: "1.0.0"
when_to_use:
  - X投稿用の縦型図解・インフォグラフィック画像を設計・プロンプト化したいとき
  - scheduled_draft_pipeline.py が生成した image_prompt を縦型図解ルールで強化したいとき
  - アカウントのキャラクターを図解画像に組み込みたいとき
  - AI活用・Claude Code・Codex・Remotion・自動化・動画制作・マーケティング系の図解画像を作るとき
  - 生成済みの図解画像を修正・改善したいとき
---

# x-vertical-infographic-creator スキル

## リポジトリ内での位置づけ

```
.agent/skills/x-vertical-infographic-creator/
├── SKILL.md                          ← このファイル
├── references/
│   ├── style-guide.md                ← カラー・レイアウトルール
│   ├── prompt-templates.md           ← 用途別プロンプトテンプレート
│   └── improvement-prompts.md        ← 生成画像の修正・改善プロンプト集
└── examples/
    └── ai-video-workflow-example.md  ← AI動画制作ワークフローの完成例

# アカウント別設定は x-post-writer と統合して管理
.agent/skills/x-post-writer/accounts/
├── gutaraAikatuyou.md                ← 投稿トンマナ（x-post-writer用）
└── gutaraaikatuyou/                  ← 図解設定サブフォルダ
    ├── design-guide.md               ← アカウント設計・デザイン方針
    ├── character-prompt.md           ← 画像生成プロンプト用キャラクター説明
    └── infographic-rules.md          ← 縦型図解ルール（パイプラインが自動注入）
```

`x-post-writer/scripts/scheduled_draft_pipeline.py` の `build_generation_prompt()` が
`x-post-writer/accounts/{x_username}/character-prompt.md` と `infographic-rules.md` を読み込んで、
`image_prompt.prompt` の生成指示に自動注入する。

他のアカウントの図解設定を追加する場合は `x-post-writer/accounts/{x_username}/` フォルダを作成し、
`character-prompt.md` と `infographic-rules.md` を置くだけで自動的に反映される。

---

## スキルの目的

「ただ綺麗な図解」ではなく、**Xでスクロール中に目を止めさせる"強い1枚"** を作る。

- 怪しい情報商材感・過度な煽り・黒背景×赤文字には寄せない
- 爽やかで信頼感のあるブルー基調を優先する
- アカウントのキャラクターを補助要素として組み込む

---

## 使い方

### A. パイプライン経由（自動）

`scheduled_draft_pipeline.py` 実行時に `accounts/{account}/character-prompt.md` が
`build_generation_prompt()` に自動注入される。追加操作は不要。

### B. 手動で図解プロンプトを作る

ユーザーから以下を受け取る（任意の組み合わせでOK）：

| 入力 | 必須 |
|------|------|
| 投稿文 / ツリー | いずれか必須 |
| メモ / コンセプト | 任意 |
| アカウント名 | 必須（キャラクター情報の読み込みに使う） |
| 改善対象の画像プロンプト | 改善依頼の場合 |

手順：
1. `x-post-writer/accounts/{account}/design-guide.md` を読み込んでデザイン方針を把握する
2. `x-post-writer/accounts/{account}/character-prompt.md` を読み込んでキャラクター情報を把握する
3. 図解コンセプトを設計する（→ 出力フォーマット参照）
4. `references/prompt-templates.md` のテンプレートを使って完成プロンプトを出力する
5. 必要なら `references/improvement-prompts.md` から修正プロンプトを選択・提示する

---

## ワークフロー

### STEP 1 — 情報整理

| 分類 | 基準 |
|------|------|
| **入れる** | 強い見出し・流れ（3〜4ステップ）・結論 |
| **削る** | 長い説明・細かい数値・全ツリー内容 |
| **強調** | 変化のポイント・最も驚く事実・行動喚起ワード |
| **結論** | 読者が1枚で持ち帰るメッセージ（1行） |

**1枚に入れる項目は最大7個まで。9項目以上は禁止。**

### STEP 2 — 図解コンセプト設計

- **何を一瞬で伝えるか** — 1行で言えるメッセージ
- **誰に刺すか** — ターゲット像
- **見た人にどんな感情を起こすか** — 「試したい」「自分もできそう」「こんな世界があるのか」等

### STEP 3 — レイアウト設計

縦型 9:16 基本。X投稿・スマホ閲覧前提。

```
┌────────────────────────────┐
│  [上部]                     │
│  大見出し（インパクト重視）    │
│  サブ見出し                  │
│                   [キャラ]  │
├────────────────────────────┤
│  [中央]                     │
│  3〜4ステップのフロー        │
│  白カード + 矢印 + アイコン   │
├────────────────────────────┤
│  [下部]                     │
│  結論（大きく）              │
│  補足（小さく1行）           │
└────────────────────────────┘
```

キャラクター配置：上部右側 または 右下。図面積の20〜25%以内。

### STEP 4 — プロンプト生成

`references/prompt-templates.md` のテンプレートを使い、英語中心で出力する。
日本語テキスト指定は1行あたり **10〜16文字以内**。

### STEP 5 — 改善プロンプト

`references/improvement-prompts.md` から状況に応じた修正指示を提示する。

---

## 出力フォーマット

```markdown
## 図解コンセプト
- 何を伝えるか：
- 誰に刺すか：
- 起こしたい感情：

## 情報整理
- 入れる：
- 削る：
- 強調：
- 結論：

## レイアウト案
[上部] 大見出し / サブ見出し
[中央] ステップ一覧
[下部] 結論
キャラクター配置: 上部右側（図面積の約20%）

## 画像生成プロンプト（そのまま使える完成版）
（英語中心のプロンプト本文）

## 改善プロンプト
- 怪しい場合：
- 情報過多の場合：
- 文字崩れの場合：
```

---

## デザインルール（詳細は `references/style-guide.md`）

### 推奨カラー

| 用途 | カラー |
|------|--------|
| 背景 | `#EAF6FF` / `#F5FBFF` / `#DFF3FF` |
| メインブルー | `#2563EB` |
| ディープブルー | `#1E3A8A` |
| シアンアクセント | `#38BDF8` |
| イエローアクセント | `#FACC15`（強調1点のみ） |
| ホワイトカード | `#FFFFFF` |
| テキストネイビー | `#0F172A` |

### 必ず避けること

- 黒背景メイン / 赤文字メイン / 強すぎるネオン
- 情報商材感 / 危機感だけを煽る文言
- 9項目以上の情報 / 文字だらけのレイアウト

---

## 品質チェックリスト

- [ ] 1枚で伝えたいことが **1行で言える** か
- [ ] 画像内テキストが **合計7項目以内** か
- [ ] 日本語テキストが **1行16文字以内** か
- [ ] 黒背景・赤文字・ネオンが **含まれていない** か
- [ ] キャラクターが **図解の邪魔をしていない** か（面積20〜25%以内）
- [ ] 結論が **下部に大きく** 配置されているか
- [ ] プロンプトに **`vertical 9:16`** 指定が入っているか
- [ ] アカウントの `character-prompt.md` が **反映されている** か
