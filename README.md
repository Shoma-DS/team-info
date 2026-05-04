# Docker 起動ガイド

スタッフは以下だけ実行すればよいです。

Mac / Linux:

```bash
./run.sh
```

Windows:

```powershell
./run.ps1
```

## このスクリプトがやること

- Docker CLI の有無を確認する
- Docker Desktop 未インストールなら案内を表示して Enter 待ちする
- Docker Engine が未起動なら Docker Desktop の起動を試みる
- Docker Engine が利用可能になるまで待機する
- `docker compose` を実行する

## compose 対象の決まり方

- 今いるディレクトリに `docker-compose.yml` / `docker-compose.yaml` / `compose.yml` / `compose.yaml` があれば、そのディレクトリで実行する
- repo ルートで実行した場合は、既知の compose プロジェクトから選ぶ
  - `docker/n8n`
  - `docker/dify/docker`
- `--project n8n` または `--project dify` を付けると、対象を固定できる
- `--action up|down|stop|start|restart|ps` を付けると、同じ入口から停止や状態確認もできる

## 補足

- Docker Desktop が既に起動している場合は、そのまま `docker compose up` へ進む
- 追加オプションを渡したい場合は、そのまま後ろに付けられる

Mac / Linux:

```bash
./run.sh -d
./run.sh --project dify -d
./run.sh --project dify --action down
./run.sh --project dify --action ps
```

Windows:

```powershell
./run.ps1 -d
./run.ps1 -Project dify -d
./run.ps1 -Project dify -Action down
./run.ps1 -Project dify -Action ps
```

## Docker Desktop を使わない Windows 運用

Windows で Docker Desktop を使わない場合は、WSL2 Ubuntu 側に Docker Engine + Compose v2 を入れて、`run.ps1` から WSL 内の `docker compose` を呼び出します。

```powershell
& "$env:TEAM_INFO_ROOT\setup\setup_wsl_docker_engine.ps1" -Distro Ubuntu
```

セットアップ後、PowerShell を開き直すか `wsl --shutdown` を実行してから、通常どおり次を使います。

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project dify -d
& "$env:TEAM_INFO_ROOT\run.ps1" -Project dify -Action ps
```

複数の WSL distro がある場合は、利用する distro 名を固定できます。

```powershell
[System.Environment]::SetEnvironmentVariable("TEAM_INFO_WSL_DISTRO", "Ubuntu", "User")
```
