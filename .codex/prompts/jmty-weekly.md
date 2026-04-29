---
description: "jmty-weekly コマンドを CEO 経由で起動する"
argument-hint: "[EXTRA=\"free-form note\"]"
---

この prompt / command は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。
このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、`/jmty-weekly` のルールを確認してください。
次に `.agent/skills/common/agent-org-ceo/SKILL.md` を読み込み、そのスキルとして動作してください。
CEO としてこの依頼を受け付け、`/jmty-weekly` の意味に応じて必要な専門スキルや週次ワークフロープロンプトへ委譲してください。
手動実行しやすいように、必要なら `personal/deguchishouma/scripts/jmty-banner-codex/prompts/weekly_jmty_banner_prompt.md` を読み、その内容に沿って進めてください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
