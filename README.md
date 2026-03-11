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
- `docker compose up` を実行する

## compose 対象の決まり方

- 今いるディレクトリに `docker-compose.yml` / `docker-compose.yaml` / `compose.yml` / `compose.yaml` があれば、そのディレクトリで実行する
- repo ルートで実行した場合は、既知の compose プロジェクトから選ぶ
  - `docker/n8n`
  - `docker/dify/docker`
- `--project n8n` または `--project dify` を付けると、対象を固定できる

## 補足

- Docker Desktop が既に起動している場合は、そのまま `docker compose up` へ進む
- 追加オプションを渡したい場合は、そのまま後ろに付けられる

Mac / Linux:

```bash
./run.sh -d
./run.sh --project dify -d
```

Windows:

```powershell
./run.ps1 -d
./run.ps1 -Project dify -d
```
