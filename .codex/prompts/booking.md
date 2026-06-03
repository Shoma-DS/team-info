---
description: "候補日時からGoogleカレンダー予定を作成し、返信文を生成する"
argument-hint: "[候補日時メッセージや予定タイトル]"
---

この prompt / command は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。
このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、`/booking` のルールを確認してください。
次に `.agent/skills/common/agent-org-ceo/SKILL.md` を読み込み、そのスキルとして動作してください。
CEO としてこの依頼を受け付け、`/booking` の意味に応じて `.agent/skills/common/calendar-booking-reply/SKILL.md` へ委譲してください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
