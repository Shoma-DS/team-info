# Docker self-host (n8n + Dify)

このディレクトリで、`n8n` と `Dify` をローカルホスト上で動かせます。

## 1) n8n

### 初回

```bash
cd docker/n8n
cp .env.example .env
docker compose up -d
```

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
- `docker compose up -d` を実行

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

```bash
# macOS
open -a Docker
```

Docker が起動してから再実行:

```bash
cd docker/dify/docker
docker compose up -d
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
