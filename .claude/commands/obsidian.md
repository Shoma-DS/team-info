これは Claude Code 用の互換ラッパーです。正本は `AGENTS.md` と `.agent/skills/common/agent-org-ceo/SKILL.md` です。

まず `AGENTS.md` を読み、`/obsidian` のルールを確認してください。
次に `.agent/skills/common/agent-org-ceo/SKILL.md` を読み込み、agent-org-ceo スキルとして動作してください。
CEO としてこの依頼を受け付け、`/obsidian` の意味に応じて `.agent/skills/common/team-info-setup/obsidian-claudian/SKILL.md` へ委譲してください。
委譲後は、Obsidian が導入されているPCだけで `team_info_obsidian_claudian.py bootstrap` を標準入口として使い、Gitアカウント別の `personal/<account>/obsidian/claude-obsidian/` に個人知識を溜める方針で進めてください。
Codex 連携用の `--setup-multi-agent` は、ホーム配下へ symlink を作るため、実行前にユーザー確認を取ってください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください。
