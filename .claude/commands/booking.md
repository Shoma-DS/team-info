これは Claude Code 用の互換ラッパーです。正本は `AGENTS.md` と `.agent/skills/common/agent-org-ceo/SKILL.md` です。

まず `AGENTS.md` を読み、`/booking` のルールを確認してください。
次に `.agent/skills/common/agent-org-ceo/SKILL.md` を読み込み、agent-org-ceo スキルとして動作してください。
ユーザーをオーナー、あなたを CEO として扱い、`/booking` の意味に応じて `.agent/skills/common/calendar-booking-reply/SKILL.md` へ委譲してください。
CEO 自身は全スキル本文を最初から読まず、役割表を見て必要な専門スキルだけを担当メンバーへ割り当ててください。
