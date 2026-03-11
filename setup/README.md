# team-info セットアップ

このフォルダのスクリプトで、macOS/Windows に同じ開発環境を構築できます。

## インストールされるもの

| カテゴリ | 内容 |
|---------|------|
| Python | 3.11.9 (ホスト側の起動用) + Docker ランタイム `team-info/python-skill-runtime:3.11.9` |
| Python パッケージ | Whisper, OpenCV, MediaPipe, JAX, Remotion スクリプト等を Docker イメージへ固定 |
| Node.js | 22.17.1 と Dify 用 Node 24 系 (`nvm` / `nvm-windows` 経由) |
| npm パッケージ | Remotion, VOICEVOX MCP, Canva補助, Dify Web/SDK |
| その他 | Git, FFmpeg, Tesseract OCR, macOS では `tesseract-lang`, `uv`, Docker, VOICEVOX Engine コンテナ |

---

## まずはこれを実行

このリポジトリでは、入口を 1 本にまとめました。

### macOS

```bash
bash ./setup/setup_all.cmd
```

### Windows

```powershell
.\setup\setup_all.cmd
```

この入口は、`team-info` のリポジトリルートをカレントディレクトリにした状態で実行する前提です。
セットアップ中の `TEAM_INFO_ROOT` は、まずそのカレントディレクトリを見て、repo root と判断できるときはその値を使います。違う場所から起動した場合だけ、スクリプト自身の位置から推定します。

この入口が OS に合わせて中のセットアップを呼び分けます。
- macOS は `setup_mac.sh`
- Windows は `setup_windows.ps1`
- 最後に共通の `verify_setup.py` を走らせ、依存関係と Docker ランタイムまで確認します
- 検証に失敗した場合は、`setup_all.cmd` 全体が非 0 で終了します
- `TEAM_INFO_ROOT` もあわせて保存します
- macOS では `~/.config/team-info/env.sh`、シェル初期化ファイル、`launchctl` に保存します
- Windows ではユーザー環境変数として保存します
- Windows では内部で PowerShell を `Bypass` 付きで呼ぶため、まずはこの入口だけで進められます
- できる範囲で Dify 開発用の `uv` / `pnpm` / Node 24 も準備します
- Canva 用の `~/.secrets/canva_credentials.txt` ひな形も作ります

---

## 個別に実行したいとき

### macOS

```bash
bash "[team-info を置いた絶対パス]/setup/setup_mac.sh"
```

- Homebrew → pyenv → Python 3.11.9 → Docker ランタイム → nvm → Node.js → npm の順で自動インストール
- Apple Silicon (M1/M2/M3) は `jax[metal]`、Intel Mac は `jax[cpu]` を自動選択
- `Remotion/scripts/canva_auth` と `docker/dify` の依存も入れます
- `tesseract-lang` も追加で入れます
- 最後に `setup/verify_setup.py` で `TEAM_INFO_ROOT`、host venv、npm 依存、Docker runtime import を検証します

### Windows

PowerShell を**管理者として**開いて実行:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
& "[team-info を置いた絶対パス]\setup\setup_windows.ps1"
```

- winget → pyenv-win → Python 3.11.9 → Docker ランタイム → nvm-windows → Node.js → npm の順で自動インストール
- `jax[cpu]` をインストール
- `Remotion/scripts/canva_auth` と `docker/dify` の依存も入れます
- `uv` は Python 経由で入れます
- 最後に `setup/verify_setup.py` で `TEAM_INFO_ROOT`、host venv、npm 依存、Docker runtime import を検証します

---

## まだ手で必要なもの

- Canva の `CANVA_CLIENT_ID` と `CANVA_CLIENT_SECRET` を `~/.secrets/canva_credentials.txt` に書くこと
- Docker Desktop 本体のインストール

自動セットアップだけで土台はかなりそろいますが、外部サービスの認証は別作業です。

---

## Docker Python ランタイムの標準運用

Python/スクリプト系スキルは、原則として次の共通ランタイム経由で動かします。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" run-remotion-python -- \
  "[repo 内の Python スクリプト絶対パス]" [引数...]
```

Docker イメージを手動で再ビルドしたい場合:

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" build-remotion-python
```

VOICEVOX は GUI 版ではなく Docker 上の Engine を使います。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" start-voicevox-engine
```

`Dify` や `n8n` を起動するときは、素の `docker compose up` ではなく共通ランチャーを使います。

```bash
bash "$TEAM_INFO_ROOT/run.sh" --project dify -d
```

Windows:

```powershell
& "$env:TEAM_INFO_ROOT\run.ps1" -Project dify -d
```

---

## Python venv の手動有効化（非常用のホスト実行）

標準は Docker です。`TEAM_INFO_PYTHON_RUNTIME=host` を使う非常時だけ有効化してください。

```bash
# macOS
source "$TEAM_INFO_ROOT/Remotion/.venv/bin/activate"

# Windows
[team-info を置いた絶対パス]\Remotion\.venv\Scripts\Activate.ps1
```

---

## requirements.txt の更新

Docker ランタイムに入れる依存は `setup/requirements.txt` を編集し、次を実行します。

```bash
python "$TEAM_INFO_ROOT/.agent/skills/common/scripts/team_info_runtime.py" build-remotion-python
```
