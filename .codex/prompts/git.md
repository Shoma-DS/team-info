---
description: "git-workflow に従ってコミットと push を行う。Discord 報告は送るか確認する"
argument-hint: "[EXTRA=\"free-form note\"]"
---

この prompt / command は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。
このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、`/git` のルールを確認してください。
次に `.agent/skills/common/git-workflow/SKILL.md` を読み込み、そのスキルとして動作してください。
このコマンドでは push / PR のあとに Discord 報告を送るかユーザーに確認してください。
ユーザーが送ると言ったときだけ `discord-git-report` を実行してください。
報告を送る可能性があるので、push / PR の前に `origin/main` の SHA を控えておいてください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
