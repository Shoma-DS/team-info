# team-info セットアップ

`setup/` は、最初の 1 回で全部を入れ切る方式から、`core setup + skill ごとの初回自動準備` へ寄せています。

## いまの方針

- `setup/setup_all.cmd` では、日常作業の土台だけを入れる
- 重い依存や用途限定の依存は、対応する skill を初めて使うときにだけ準備する
- `setup/verify_setup.py` も、Docker image や npm 依存の総当たりではなく、core setup と lazy bootstrap の入口がそろっているかを確認する

## core setup で入るもの

| カテゴリ | 内容 |
|---------|------|
| Git | `git`, `git-lfs`, `gh` |
| Python | 3.11.9 |
| Python 補助 | `uv` |
| Node.js | 22.17.1 (`nvm` / `nvm-windows`) |
| CLI | `@openai/codex` |
| repo 設定 | `TEAM_INFO_ROOT`, `.githooks`, worked-before 記録 |

## core setup で入れないもの

以下は setup 本体では入れません。必要な skill を初めて使うタイミングで準備します。

- Remotion / VOICEVOX / Docker Python runtime
- Agent Reach / OpenClaw 連携
- Obsidian / Claudian
- clone-website 用の Node 24 workspace 依存
- Canva 補助や Dify 開発依存
- shared-agent-assets の同期処理

## まずはこれを実行

このリポジトリでは、入口を `setup/setup_all.cmd` に統一しています。

### macOS

```bash
bash ./setup/setup_all.cmd
```

### Windows

```powershell
.\setup\setup_all.cmd
```

- この最初のコマンドだけは、repo root をカレントディレクトリにした状態で相対パス案内を使ってよい運用です
- setup 側はカレントディレクトリが repo root なら、その値を `TEAM_INFO_ROOT` として保存します
- 最後に `setup/verify_setup.py` を走らせ、core setup と lazy bootstrap 入口の整合を確認します

## 個別実行したいとき

### macOS

```bash
bash "$TEAM_INFO_ROOT/setup/setup_mac.sh"
```

### Windows

```powershell
& "$env:TEAM_INFO_ROOT\setup\setup_windows.ps1"
```

## skill ごとの初回準備

### Remotion / VOICEVOX 系

- `run-remotion-python` が Docker Python runtime を必要時に準備します
- VOICEVOX は必要時だけ `start-voicevox-engine` を使います

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "[repo 内の Python スクリプト絶対パス]" [引数...]
```

### Agent Reach / OpenClaw

- `team_info_agent_reach.py` が依存不足を検出したら、初回だけ自動 bootstrap します
- 明示的にやりたい場合だけ installer を直接呼びます

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" doctor
```

### Obsidian / Claudian

- 必要になったタイミングで `/claudian` または installer script を実行します
- install は Obsidian CLI 有効化、Claudian 配備、`claudian-settings.json` 初期化、初期 subagent 雛形の seed まで行います

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/obsidian-claudian/scripts/team_info_obsidian_claudian.py" install --skip-if-no-vault
```

### clone-website

- global setup では Node 24 を固定しません
- 複製 workspace を作るときだけ template を初期化し、その workspace で Node 24 を使います

```bash
python "$TEAM_INFO_ROOT/.agent/skills/web-design/clone-website/scripts/init_clone_website_template.py" \
  "$TEAM_INFO_ROOT/outputs/web-clones/<slug>"
```

### shared-agent-assets

- 共有 assets の同期は必要時だけ手動で走らせます

```bash
bash "$TEAM_INFO_ROOT/.agent/skills/common/shared-agent-assets/scripts/sync_shared_agent_repo.sh"
```

## verify が見るもの

`setup/verify_setup.py` は次を確認します。

- `node`, `npm`, `codex`, `gh`
- `git lfs`
- `gh auth status`
- `origin` URL
- `.githooks`
- `TEAM_INFO_ROOT`
- Python 3.11
- lazy bootstrap 用 script の存在
- `docker`, `obsidian`, `openclaw` は optional として警告のみ

## まだ手で必要なもの

- GitHub 招待の承認
- `gh auth login`
- Docker Desktop 本体
- 外部サービスの cookie / API key / secret
- Obsidian vault や Claudian を使う場合の実 vault 選定

## 補足

- Docker image を先に手動で作りたい場合:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" build-remotion-python
```

- `TEAM_INFO_ROOT` だけ保存し直したい場合:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" setup-local-machine --repo-root "$TEAM_INFO_ROOT"
```
