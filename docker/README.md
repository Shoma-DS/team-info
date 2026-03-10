# Docker self-host (Python runtime + n8n + Dify)

このディレクトリで、標準の Python スキル実行環境と、`n8n` / `Dify` をローカルホスト上で動かせます。

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

## 1) n8n

### 初回

Mac / Linux:

```bash
bash "$TEAM_INFO_ROOT/run.sh" --project n8n -d
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project n8n -d
```

- 既に `docker/n8n/.env` があればそのまま起動できる。
- 起動前の Docker Desktop 確認と Engine 待機は共通ランチャーが処理する。

### アクセス

- URL: `http://localhost:5678`

### よく使う操作

```bash
cd docker/n8n
docker compose ps
docker compose logs -f n8n
docker compose down
```

## 2) Dify

Dify は構成が大きいため、公式リポジトリの `docker` 構成をそのまま使います。

### 初回起動

```bash
cd docker
./setup-dify.sh
```

このスクリプトは次を行います。

- `langgenius/dify` を `docker/dify` に clone
- `docker/dify/docker/.env` が無ければ `.env.example` から作成
- 共通ランチャー `run.sh --project dify -d` を実行

### アクセス

- URL: `http://localhost:3000`

### このリポジトリで適用済みのローカル最適化

- `docker/dify/docker/.env` を調整済み
- 公開ポート: `3000`（`n8n:5678` と競合しない）
- プロファイル: `qdrant,postgresql`（`weaviate` より軽量寄り）
- `SECRET_KEY` / DB / Redis / plugin key をデフォルト値から変更済み
- `CONSOLE_*` / `APP_*` / `SERVICE_*` URL を `http://localhost:3000` に固定

### 起動前チェック（重要）

`Cannot connect to the Docker daemon` が出る場合は Docker Desktop が未起動です。

Docker が起動してから再実行する代わりに、共通ランチャーを使う:

macOS:

```bash
bash "$TEAM_INFO_ROOT/run.sh" --project dify -d
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project dify -d
```

### よく使う操作

```bash
cd docker/dify/docker
docker compose ps
docker compose logs -f
docker compose down
```

## 3) n8n と Dify を同時に使う

- `n8n`: `5678`
- `Dify`: `3000`

上記ポートは競合しないため同時起動できます。

## 4) 事前条件

- Docker Desktop (または Docker Engine + Compose v2)
- 利用可能メモリは最低 8GB 推奨（Dify が重いため）
