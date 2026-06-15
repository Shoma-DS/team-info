---
name: codex-image-gen
description: Codex サブスクリプション（ChatGPT Plus）を使い、GPT Image 2（gpt-image-1）で画像を生成するスキル。OpenAI API キー・課金 API 不要。Codex.app または codex exec CLI 経由で動作する。全エージェント共通の画像生成窓口。
metadata:
  type: skill
---

# codex-image-gen スキル

## 目的
- 画像生成タスクを Codex サブスクリプション（ChatGPT Plus）内で処理する
- `OPENAI_API_KEY` や課金 API を一切使わない
- GPT Image 2（gpt-image-1）モデルで高品質な画像を生成する
- Claude Code・Codex・Gemini など、どのエージェントからも同じ手順で呼べる共通窓口

## 前提条件
- Codex.app がログイン済みで起動していること（`/Applications/Codex.app`）
- `codex` CLI がインストールされていること（`codex --version` で確認。未インストールなら `npm install -g @openai/codex`）
- `codex doctor` で `auth mode: chatgpt` かつ `stored ChatGPT tokens: true` が出ること

## 呼び出し方

### 方法 A: ラッパースクリプト（エージェントから非インタラクティブに呼ぶ推奨方法）

```bash
python3 "$TEAM_INFO_ROOT/.agent/skills/common/codex-image-gen/scripts/codex_image_gen.py" \
  "生成したい画像の説明（日本語可）" \
  "/絶対パス/output.png" \
  "1024x1024"
```

サイズ省略時は `1024x1024`。

### 方法 B: codex exec 直接呼び出し

```bash
SOCK="$(ls /var/folders/*/T/codex-ipc/ipc-$(id -u).sock 2>/dev/null | head -1)"
codex --remote "unix://$SOCK" exec \
  "GPT Image 2 で次の画像を生成し、/絶対パス/output.png として PNG 保存してください: [プロンプト]"
```

SOCK が空の場合は Codex.app が起動していない。方法 C へ切り替える。

### 方法 C: Codex.app インタラクティブ（Codex.app が起動済みの場合）

1. Codex.app を前面に出す
2. 以下をそのままペーストして送信:

```
GPT Image 2 で次の画像を生成してください:
[プロンプト（日本語可）]

生成後、画像を右クリック → 保存 で PNG として取得してください。
```

3. 保存先をユーザーへ確認する

## エージェント向けフロー

画像生成タスクが来たとき:

1. **Codex.app の起動確認**:
   ```bash
   pgrep -x "Codex" > /dev/null && echo "起動中" || echo "停止中"
   ```
2. 起動中 → 方法 A または B を使う
3. 停止中 → ユーザーへ「Codex.app を起動してください」と伝え、起動後に方法 A/B を使う
4. 失敗した場合 → 方法 C（インタラクティブ）を案内する

## 対応サイズ
| サイズ | 用途 |
|-------|------|
| `1024x1024` | 正方形・SNS・アイコン（標準） |
| `1792x1024` | 横長・サムネイル・バナー |
| `1024x1792` | 縦長・ストーリー・ショート動画カバー |

## 出力ファイルの扱い
- 出力先は `outputs/` 配下を原則とする（例: `"$TEAM_INFO_ROOT/outputs/images/"`）
- Drive への同期が必要な場合は `gdrive-copy` スキルを使う

## 失敗時のルール（AGENTS.md ルールと共通）
- Codex.app が停止中 → ユーザーに起動を促す。自動で起動しない
- モデルが画像生成ツールを呼べない → `codex doctor` を実行してログイン状態を確認するよう案内
- 上記で解消しない → 方法 C（インタラクティブ）を案内
- **SVG・Pillow・スクリーンショット・HTML由来 PNG などでの代替生成は行わない**
- ユーザーが「モック・下書き・ローカル合成でよい」と明示した場合のみ、代替物をモックとして扱い「AI画像生成ではない」と明記する

## Google Drive コピー（生成物がある場合）

```bash
rclone copy "[出力ファイルパス]" "gdrive:1QKaUP9fvA46mINkpSR1b2wqrIBE6By0t/outputs/images/" --progress
```

rclone が未設定なら `.agent/skills/common/git-workflow/gdrive-copy/SKILL.md` の初回セットアップ手順を参照。
