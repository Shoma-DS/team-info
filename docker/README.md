# Docker self-host (Python runtime)

このディレクトリで、標準の Python スキル実行環境をローカルホスト上で動かせます。

## 0) Python Skill Runtime + VOICEVOX Engine

標準の Python/スクリプト系スキルは、ホストの `.venv` ではなく Docker ランタイム経由で実行します。

### 初回

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" build-remotion-python
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" start-voicevox-engine
```

### よく使う操作

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" voicevox-engine-status
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" stop-voicevox-engine
```

## 1) 事前条件

- Docker Engine + Compose v2

### macOS で Docker Desktop を使わない場合

Colima などの Docker Engine 互換ランタイムを使います。

```bash
brew install docker docker-compose colima
colima start
docker compose version || docker-compose version
```

OrbStack や Rancher Desktop を使う場合も、`docker info` と `docker compose version` または `docker-compose version` が通れば同じランチャーで起動できます。

### Windows で Docker Desktop を使わない場合

WSL2 Ubuntu に Docker Engine + Compose v2 を入れて使います。repo には補助スクリプトがあります。

```powershell
& "$env:TEAM_INFO_ROOT\setup\setup_wsl_docker_engine.ps1" -Distro Ubuntu
```

セットアップ後は `run.ps1` が WSL 内の Docker を検出して、Windows パスを WSL パスへ変換してから `docker compose` を実行します。

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project current -d
```
