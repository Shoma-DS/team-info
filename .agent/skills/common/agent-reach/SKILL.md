---
name: agent-reach
description: team-info 向けに取り込んだ Agent-Reach。OpenClaw / Codex から Web・SNS・動画・RSS・GitHub を横断調査し、必要なら OpenClaw skill も同期する。外部取得やログインが絡むため、ユーザー承認後に使う。
---

# agent-reach スキル

## 役割
- `Agent-Reach` を `team-info` の運用ルールに合わせて使う。
- repo 内の skill と、OpenClaw 用 skill を同じ内容で保つ。
- 永続データは workspace ではなくローカル設定ディレクトリへ保存する。

## 保存先
- 永続データ: `~/.config/team-info/agent-reach/`
- 補助 CLI: `~/.config/team-info/agent-reach/npm-global/`
- OpenClaw skill: `~/.openclaw/skills/agent-reach/`
- 一時ファイル: `/tmp/`

## 起動コマンド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" doctor
```

## 初回導入

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/install_team_info_agent_reach.py"
```

- このコマンドは Python venv の作成、Agent-Reach の基本依存導入、`agent-reach install --env=auto` の実行まで行う。
- `bird` や `mcporter` のような外部 CLI も必要に応じて入る。

## 使い方
1. 初回は `install_team_info_agent_reach.py` を実行する。
2. 導入後は `team_info_agent_reach.py doctor` で有効チャネルを確認する。
3. Cookie や API Key が必要なチャネルは、必ずユーザー承認後に `configure` を使う。
4. OpenClaw 側へ skill を入れ直したいときは `team_info_agent_reach.py skill --install` を使う。

## team-info 優先ルール
- `.agent/skills` を repo の正本とし、OpenClaw 側はこの `SKILL.md` をコピーして使う。
- 新しいログイン情報や cookie は repo 内に保存しない。
- Docker を使うチャネルは、必要時のみ起動し、不要なら停止する。
- 出力を repo に残すときは、ユーザーが明示したパスか `inputs/` / `outputs/` 配下へ整理する。

## 代表コマンド

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" doctor
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" configure twitter-cookies "auth_token=...; ct0=..."
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" configure xhs-cookies "key1=val1; key2=val2"
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" skill --install
```
