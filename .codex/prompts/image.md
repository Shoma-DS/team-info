---
description: "GPT Image 2 でサブスク内画像生成（API キー不要）"
argument-hint: "[プロンプト（日本語可）] [出力パス.png] [サイズ: 1024x1024|1792x1024|1024x1792]"
---

この prompt は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。

このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、画像生成ルールを確認してください。
次に `.agent/skills/common/codex-image-gen/SKILL.md` を読み込み、そのスキルとして動作してください。

## やること
1. Codex.app が起動しているか確認する（`pgrep -x Codex`）
2. IPC ソケットを特定する（`ls /var/folders/*/T/codex-ipc/ipc-$(id -u).sock`）
3. GPT Image 2 でユーザー指定のプロンプトから画像を生成する
4. 出力パスが指定されていれば PNG として保存する

## 引数の解釈
- 第1引数: プロンプト（省略時はユーザーに確認）
- 第2引数: 出力パス（省略時は `$TEAM_INFO_ROOT/outputs/images/` 配下へ自動命名）
- 第3引数: サイズ（省略時は `1024x1024`）

ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
