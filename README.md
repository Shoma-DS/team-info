# Docker 起動ガイド

Docker Compose を使うプロジェクトでは、compose ファイルがあるディレクトリで共通ランチャーを実行します。

Mac / Linux:

```bash
bash "$TEAM_INFO_ROOT/run.sh" --project current
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current
```

## このスクリプトがやること

- Docker CLI の有無を確認する
- Docker CLI が無ければ Docker Engine + Compose v2 の準備案内を表示して Enter 待ちする
- Docker Engine が未起動なら、利用可能な互換ランタイムの起動を試みる
- Docker Engine が利用可能になるまで待機する
- `docker compose` を実行する（環境によっては `docker-compose` にフォールバック）

## compose 対象の決まり方

- 今いるディレクトリに `docker-compose.yml` / `docker-compose.yaml` / `compose.yml` / `compose.yaml` があれば、そのディレクトリで実行する
- repo ルートには既定の compose プロジェクトを置かない
- `--project current` を付けると、現在のディレクトリを対象に固定できる
- `--action up|down|stop|start|restart|ps` を付けると、同じ入口から停止や状態確認もできる

## 補足

- Docker Desktop は必須ではありません。Docker Engine + Compose v2 が使えれば動きます
- macOS は Colima / OrbStack / Rancher Desktop / Docker Engine などを使えます
- `TEAM_INFO_DOCKER_START_COMMAND` に起動コマンドを入れると、共通ランチャーが最初に実行します
- 追加オプションを渡したい場合は、そのまま後ろに付けられる

Mac / Linux:

```bash
bash "$TEAM_INFO_ROOT/run.sh" --project current -d
bash "$TEAM_INFO_ROOT/run.sh" --project current --action down
bash "$TEAM_INFO_ROOT/run.sh" --project current --action ps
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current -d
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current -Action down
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current -Action ps
```

## Docker Desktop を使わない運用

macOS では Colima などの Docker Engine 互換ランタイムを使えます。

```bash
brew install docker docker-compose colima
colima start
docker compose version || docker-compose version
bash "$TEAM_INFO_ROOT/run.sh" --project current -d
```

Windows では、WSL2 Ubuntu 側に Docker Engine + Compose v2 を入れて、`run.ps1` から WSL 内の `docker compose` を呼び出します。

```powershell
& "$env:TEAM_INFO_ROOT\setup\setup_wsl_docker_engine.ps1" -Distro Ubuntu
```

セットアップ後、PowerShell を開き直すか `wsl --shutdown` を実行してから、通常どおり次を使います。

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current -d
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current -Action ps
```

複数の WSL distro がある場合は、利用する distro 名を固定できます。

```powershell
[System.Environment]::SetEnvironmentVariable("TEAM_INFO_WSL_DISTRO", "Ubuntu", "User")
```
