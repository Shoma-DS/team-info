# team-info 共通Docker実行環境

このディレクトリは、`team-info` リポジトリをチーム全員で同じ条件で実行するためのDocker環境です。

## 目的

- Python / Node / FFmpeg / Tesseract など、スキル実行に必要な道具を1つのコンテナに固定する
- 各PCの差（OS・ローカル設定差）を減らす
- Pythonやスクリプトを伴うスキルを、基本的にコンテナ内で実行する運用にする

## 事前準備

- Docker Desktop または Docker Engine + Compose v2 をインストール
- `TEAM_INFO_ROOT` をこのリポジトリの絶対パスに設定

## 使い方

### 1) イメージを作る

```bash
docker compose -f "$TEAM_INFO_ROOT/docker/team-info/docker-compose.yml" build
```

### 2) コンテナに入る

```bash
docker compose -f "$TEAM_INFO_ROOT/docker/team-info/docker-compose.yml" run --rm team-info bash
```

### 3) コンテナ内でスキル関連コマンドを実行

例:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" worked-before-status
python "$TEAM_INFO_ROOT/Remotion/scripts/sleep_travel_movie.py" --help
npm --prefix "$TEAM_INFO_ROOT/Remotion/my-video" run build
```

## ワンライナー実行

コンテナを毎回起動してコマンドだけ実行する場合:

```bash
docker compose -f "$TEAM_INFO_ROOT/docker/team-info/docker-compose.yml" run --rm team-info <実行したいコマンド>
```

例:

```bash
docker compose -f "$TEAM_INFO_ROOT/docker/team-info/docker-compose.yml" run --rm team-info \
  python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" owner-status
```

## 補足

- リポジトリ本体は `../..:/workspace/team-info` でマウントするため、コンテナ内で作った変更はそのままホスト側に反映されます。
- 依存のダウンロードキャッシュ（pip / npm）はDockerボリュームに保存されます。
- GPUを使う処理やVOICEVOX本体など、ホスト依存の道具は必要に応じて追加設定してください。


## 補足（改善点）

- ルートの `.dockerignore` で不要ファイルのビルド転送を減らし、ビルド時間を短縮しています。
- `scripts/docker-skill-run.sh` は `TEAM_INFO_ROOT` 未設定時にリポジトリ位置を自動推定します。
