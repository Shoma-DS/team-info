これは Claude Code 用の互換ラッパーです。正本は `AGENTS.md` の `/pull` ルールです。

`/pull` として動作してください。
`origin` から `fetch` と `pull --rebase origin main` を行い、競合が出たらユーザーに伝えて停止してください。
完了後は、ブランチ名と取り込んだコミット数、またはすでに最新である旨だけを短く報告してください。
