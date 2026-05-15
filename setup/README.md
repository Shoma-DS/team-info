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
| Cloud copy | `rclone` |
| Python | 3.11.9 |
| Python 補助 | `uv` |
| Node.js | 22.17.1 (`nvm` / `nvm-windows`) |
| CLI | `@openai/codex`, `freebuff` |
| Windows UTF-8 | PowerShell 7 (`pwsh`), `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` |
| repo 設定 | `TEAM_INFO_ROOT`, `.githooks`, worked-before 記録 |

## core setup で入れないもの

以下は setup 本体では入れません。必要な skill を初めて使うタイミングで準備します。

- Remotion / VOICEVOX / Docker Python runtime
- Agent Reach / OpenClaw 連携
- Obsidian / Claudian
- clone-website 用の Node 24 workspace 依存
- Canva 補助などの追加開発依存
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

## 課金なしで AI エージェントを使う

setup 後は、課金なしの AI コーディングエージェントとして `freebuff` を使えます。
Codebuff 系の無料 CLI で、広告付きのためサブスクやクレジット設定なしで起動できます。

```bash
cd "$TEAM_INFO_ROOT"
freebuff
```

Windows:

```powershell
Set-Location $env:TEAM_INFO_ROOT
freebuff
```

既存の `codex` は Codex CLI を使う人向け、`freebuff` は未課金メンバー向けの入口として使い分けます。

macOS で `/usr/local/lib/node_modules` に書き込めない場合、setup は自動で `$HOME/.local` を npm の退避先として使います。
手動で直す場合は次を実行します。

```bash
mkdir -p "$HOME/.local" "$HOME/.local/bin" && NPM_CONFIG_PREFIX="$HOME/.local" npm install -g freebuff
```

Windows で npm の global install 先に書き込めない場合、setup は自動で `%USERPROFILE%\.local\npm` を退避先として使います。
手動で直す場合は次を実行します。

```powershell
$env:NPM_CONFIG_PREFIX = "$env:USERPROFILE\.local\npm"; npm install -g freebuff
```

## Windows の日本語 / UTF-8 対策

Windows では setup 時に PowerShell 7 (`pwsh`) を導入し、Python 系の文字化け対策として `PYTHONUTF8=1` と `PYTHONIOENCODING=utf-8` をユーザー環境変数へ保存します。

- 初回 setup は従来どおり `.\setup\setup_all.cmd` で実行します
- 2回目以降、`pwsh` が入っていれば `setup_all.cmd` は自動で PowerShell 7 を使います
- 日本語を含む作業や UTF-8 のファイル操作は、Windows PowerShell 5.1 ではなく `pwsh` で行う前提にします

## skill ごとの初回準備

### Remotion / VOICEVOX 系

- `run-remotion-python` が Docker Python runtime を必要時に準備します
- VOICEVOX は必要時だけ `start-voicevox-engine` を使います
- Remotion の字幕・フック・見出しの粗編集は `my-video/src/textLayout.ts` に集約しています
- `textLayout.ts` では BudouX を使って日本語の自然な改行を決めています
- `my-video` の `npm install` に BudouX が含まれるので、setup 本体で別途入れる必要はありません

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

- 必要になったタイミングで `/obsidian` または installer script を実行します
- `ensure-vault` は各PCのGitアカウント名に合わせて `personal/<account>/obsidian/claude-obsidian/` を作成・初期化します
- `install` は Obsidian CLI 有効化、Claudian 配備、`claudian-settings.json` 初期化、初期 subagent 雛形の seed まで行います

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" ensure-vault
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" install --skip-if-no-vault
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
- 引数を省略した場合は `TEAM_INFO_SHARED_AGENT_ASSETS_ROOT`、または sibling の `shared-agent-assets` / `shared-rules-repo` を自動で探します

```bash
bash "$TEAM_INFO_ROOT/.agent/skills/common/shared-agent-assets/scripts/sync_shared_agent_repo.sh"
```

- 明示パスで同期したい場合:

```bash
bash "$TEAM_INFO_ROOT/.agent/skills/common/shared-agent-assets/scripts/sync_shared_agent_repo.sh" "/absolute/path/to/shared-agent-assets"
```

### Google Drive / rclone

- `rclone` は core setup で入ります
- Google Drive の `gdrive` remote は、`/gdrive` を初めて使うときに `rclone config` で作ります
- アップロード先は `team-info/outputs/` 配下のフォルダです

## verify が見るもの

`setup/verify_setup.py` は次を確認します。

- `node`, `npm`, `codex`, `freebuff`, `gh`
- `rclone`
- Windows では `pwsh`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`
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
- Google Drive の `gdrive` remote 初回認証（`rclone config`）
- Docker Engine + Compose v2（Docker Desktop は必須ではない）
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
