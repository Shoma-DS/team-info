---
description: "X投稿下書き生成・ブックマーク取得フローを起動する"
argument-hint: "[EXTRA=\"補足メモ\"]"
---

この prompt / command は `team-info` リポジトリ専用です。
まずカレントディレクトリに `AGENTS.md` があり、その内容が `team-info` 用であることを確認してください。
もし `AGENTS.md` が見つからない、または別リポジトリだと分かった場合は、その旨を短く伝えて停止してください。
このリポジトリでは `AGENTS.md` が正本です。
まず `AGENTS.md` を読み、`/x` のルールを確認してください。
次に `.agent/skills/x-post-writer/SKILL.md` を読み込み、そのスキルとして動作してください。
`bookmarks_latest.json` に `account_profile.account_file_path` が入っている場合は、
その `accounts/*.md` を最優先で読み、アカウント取り違えを避けてください。
ユーザーが追加の引数や補足を付けた場合は、それも考慮してください: $ARGUMENTS
