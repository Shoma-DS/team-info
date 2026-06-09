---
description: "コミットのみを行う"
argument-hint: "[EXTRA=\"free-form note\"]"
---

この prompt / command は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。
このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、`/c` のルールを確認してください。
このコマンドはコミットのみです。push と PR 作成は行わないでください。
コミットメッセージや Git の安全ルールは `.agent/skills/common/git-workflow/SKILL.md` に従ってください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
