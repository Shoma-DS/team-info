---
description: "obsidian コマンドを CEO 経由で起動する"
argument-hint: "[EXTRA=\"free-form note\"]"
---

この prompt / command は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。
このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、`/obsidian` のルールを確認してください。
次に `.agent/skills/common/agent-org-ceo/SKILL.md` を読み込み、そのスキルとして動作してください。
CEO としてこの依頼を受け付け、`/obsidian` の意味に応じて `.agent/skills/common/team-info-setup/obsidian-claudian/SKILL.md` へ委譲してください。
委譲後は、Obsidian が導入されているPCだけで `team_info_obsidian_claudian.py bootstrap` を標準入口として使い、Gitアカウント別の `personal/<account>/obsidian/claude-obsidian/` に個人知識を溜める方針で進めてください。
Codex からも claude-obsidian skills を使えるようにする `--setup-multi-agent` は、ホーム配下へ symlink を作るため、実行前にユーザー確認を取ってください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
