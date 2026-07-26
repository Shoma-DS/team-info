# team-info セットアップ

`setup/` は、最初の 1 回で全部を入れ切る方式から、`core setup + skill ごとの初回自動準備` へ寄せています。

## 方針

- OS 別 setup (`setup/setup_mac.sh` / `setup/setup_windows.ps1` / `setup/setup_git_bash.sh`) では、日常作業の土台だけを入れます。
- 重い依存や用途限定の依存は、対応する skill を初めて使うときに準備します。
- `setup/verify_setup.py` は、core setup と lazy bootstrap の入口がそろっているかを確認します。

## core setup で入るもの

| カテゴリ | 内容 |
|---------|------|
| Git | `git`, `git-lfs`, `gh` |
| Cloud copy | `rclone` |
| Python | 3.11.9 |
| Python 補助 | `uv` |
| Node.js | 22.17.1 (`nvm` / `nvm-windows`) |
| CLI | `@openai/codex`, `freebuff` |
| Google Workspace | `@googleworkspace/cli` (`gws`) と OAuth 認証 |
| AI proxy | Headroom token compression proxy (`claude` / `codex` routing; failure is non-fatal) |
| Windows UTF-8 | PowerShell 7 (`pwsh`), `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` |
| repo 設定 | `TEAM_INFO_ROOT`, `.githooks`, worked-before 記録 |

## core setup で入れないもの

以下は setup 本体では入れません。必要な skill を初めて使うタイミングで準備します。

- Remotion / VOICEVOX / Docker Python runtime
- Agent Reach / OpenClaw 連携
- Obsidian / Claudian
- clone-website 用の Node 24 workspace 依存
- Canva など外部サービスの秘密情報
- shared-agent-assets の同期

## 初回実行

この最初のコマンドだけは、repo root をカレントディレクトリにした状態で相対パス案内を使ってよい運用です。
setup 側はカレントディレクトリが repo root なら、その値を `TEAM_INFO_ROOT` として保存します。

macOS:

```bash
bash ./setup/setup_mac.sh
```

Windows:

```powershell
.\setup\setup_windows.ps1
```

Windows Git Bash:

```bash
bash ./setup/setup_git_bash.sh
```

最後に `setup/verify_setup.py` が走り、core setup と lazy bootstrap 入口の整合を確認します。

## 個別実行

macOS:

```bash
bash "$TEAM_INFO_ROOT/setup/setup_mac.sh"
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\setup\setup_windows.ps1"
```

Windows Git Bash:

```bash
bash "$TEAM_INFO_ROOT/setup/setup_git_bash.sh"
```

## 課金なしで AI エージェントを使う

setup 後は、課金なしの AI コーディングエージェントとして `freebuff` を使えます。
既存の `codex` は Codex CLI を使う人向け、`freebuff` は未課金メンバー向けの入口です。

```bash
freebuff
```

Windows:

```powershell
freebuff
```

macOS `/usr/local/lib/node_modules` に書き込めない場合、setup は自動で `$HOME/.local` を npm の退避先として使います。
Windows で npm の global install 先に書き込めない場合、setup は自動で `%USERPROFILE%\.local\npm` を退避先として使います。

## Google Workspace CLI 認証

setup では `@googleworkspace/cli` を入れ、`gws auth status` を確認します。
未認証、または GWS CLI で使う主要サービスのスコープが不足している可能性がある場合は、ブラウザ認証へ進みます。

手動でやり直す場合:

```bash
gws auth login -s drive,sheets,gmail,calendar,docs,slides,tasks,script
```

Windows / Windows Git Bash も同じコマンドです。

## Headroom token compression proxy

setup 後は、`claude` / `codex` がローカルの Headroom proxy 経由になります。
macOS / Windows の通常 setup に組み込み済みで、失敗しても setup 全体は止めず warning として続行します。

確認:

```bash
bash "$TEAM_INFO_ROOT/setup/headroom/check.sh"
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\setup\headroom\check.ps1"
```

詳細、手動導入、ロールバックは `setup/headroom/README.md` を参照してください。

## Windows の日本語 / UTF-8 対策

Windows では setup 時に PowerShell 7 (`pwsh`) を導入し、Python 系の文字化け対策として `PYTHONUTF8=1` と `PYTHONIOENCODING=utf-8` をユーザー環境変数へ保存します。
日本語を含む作業や UTF-8 のファイル操作は、Windows PowerShell 5.1 ではなく `pwsh` で行う前提にします。

## skill ごとの初回準備

### Remotion / VOICEVOX 系

- `run-remotion-python` が Docker Python runtime を必要時に準備します。
- VOICEVOX は必要時だけ `start-voicevox-engine` を使います。
- Remotion の字幕・フック・見出しの粗編集は `Remotion/my-video/src/textLayout.ts` に集約しています。
- `textLayout.ts` では BudouX を使って日本語の自然な改行を決めています。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- "[repo 内の Python スクリプト絶対パス]" [引数...]
```

### Agent Reach / OpenClaw

`team_info_agent_reach.py` が依存不足を検出したら、初回だけ自動 bootstrap します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/agent-reach/scripts/team_info_agent_reach.py" doctor
```

### Obsidian / Claudian

必要になったタイミングで `/obsidian` または installer script を実行します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" ensure-vault
python "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/obsidian-claudian/scripts/team_info_obsidian_claudian.py" install --skip-if-no-vault
```

### clone-website

global setup では Node 24 を固定しません。
複製 workspace を作るときだけ template を初期化し、その workspace で Node 24 を使います。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/web-design/clone-website/scripts/init_clone_website_template.py" "$TEAM_INFO_ROOT/outputs/web-clones/<slug>"
```

### shared-agent-assets

共有 assets の同期は必要時だけ手動で走らせます。

```bash
bash "$TEAM_INFO_ROOT/.agent/skills/common/team-info-setup/shared-agent-assets/scripts/sync_shared_agent_repo.sh"
```

### Google Drive / rclone

- `rclone` は core setup で入ります。
- Google Drive の `gdrive` remote は、`/gdrive` を初めて使うときに `rclone config` で作ります。
- アップロード先は `team-info/outputs/` 配下のフォルダです。

## verify が見るもの

`setup/verify_setup.py` は次を確認します。

- `node`, `npm`, `codex`, `freebuff`, `gh`
- `gws` と `gws auth status`
- `rclone`
- Windows では `pwsh`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`
- `git lfs`
- `gh auth status`
- `origin` URL
- `.githooks`
- `TEAM_INFO_ROOT`
- Python 3.11
- lazy bootstrap 用 script の存在
- Headroom installer / check script / proxy health
- `docker`, `obsidian`, `openclaw` は optional として警告のみ

## まだ手で必要なもの

- GitHub 招待の承認
- `gh auth login`
- Google Drive の `gdrive` remote 初回認証 (`rclone config`)
- Docker Engine + Compose v2
- 外部サービスの cookie / API key / secret
- Obsidian vault や Claudian を使う場合の実 vault 選定

## 補足

Docker image を先に手動で作りたい場合:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" build-remotion-python
```

`TEAM_INFO_ROOT` だけ保存し直したい場合:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" setup-local-machine --repo-root "$TEAM_INFO_ROOT"
```
