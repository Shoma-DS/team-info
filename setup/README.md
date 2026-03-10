# team-info セットアップ

このフォルダのスクリプトで、macOS/Windows に同じ開発環境を構築できます。

## インストールされるもの

| カテゴリ | 内容 |
|---------|------|
| Python | 3.11.9 (pyenv 経由) + venv (`Remotion/.venv`) |
| Python パッケージ | Whisper, OpenCV, MediaPipe, JAX, Remotion スクリプト等 |
| Node.js | 22.17.1 と Dify 用 Node 24 系 (`nvm` / `nvm-windows` 経由) |
| npm パッケージ | Remotion, VOICEVOX MCP, Canva補助, Dify Web/SDK |
| その他 | Git, FFmpeg, Tesseract OCR, macOS では `tesseract-lang`, `uv`, Docker (確認のみ) |

---

## まずはこれを実行

このリポジトリでは、入口を 1 本にまとめました。

### macOS

```bash
bash "[team-info を置いた絶対パス]/setup/setup_all.cmd"
```

### Windows

```powershell
& "[team-info を置いた絶対パス]\setup\setup_all.cmd"
```

この入口が OS に合わせて中のセットアップを呼び分けます。
- macOS は `setup_mac.sh`
- Windows は `setup_windows.ps1`
- `TEAM_INFO_ROOT` もあわせて保存します
- Windows では内部で PowerShell を `Bypass` 付きで呼ぶため、まずはこの入口だけで進められます
- できる範囲で Dify 開発用の `uv` / `pnpm` / Node 24 も準備します
- Canva 用の `~/.secrets/canva_credentials.txt` ひな形も作ります

---

## 個別に実行したいとき

### macOS

```bash
bash "[team-info を置いた絶対パス]/setup/setup_mac.sh"
```

- Homebrew → pyenv → Python 3.11.9 → venv → pip パッケージ → nvm → Node.js → npm の順で自動インストール
- Apple Silicon (M1/M2/M3) は `jax[metal]`、Intel Mac は `jax[cpu]` を自動選択
- `Remotion/scripts/canva_auth` と `docker/dify` の依存も入れます
- `tesseract-lang` も追加で入れます

### Windows

PowerShell を**管理者として**開いて実行:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
& "[team-info を置いた絶対パス]\setup\setup_windows.ps1"
```

- winget → pyenv-win → Python 3.11.9 → venv → pip パッケージ → nvm-windows → Node.js → npm の順で自動インストール
- `jax[cpu]` をインストール
- `Remotion/scripts/canva_auth` と `docker/dify` の依存も入れます
- `uv` は Python 経由で入れます

---

## まだ手で必要なもの

- VOICEVOX 本体アプリのインストールと起動
- Canva の `CANVA_CLIENT_ID` と `CANVA_CLIENT_SECRET` を `~/.secrets/canva_credentials.txt` に書くこと
- Docker Desktop 本体のインストール

自動セットアップだけで土台はかなりそろいますが、外部サービスの認証や GUI アプリ本体は別作業です。

---

## Python venv の手動有効化

```bash
# macOS
source "$TEAM_INFO_ROOT/Remotion/.venv/bin/activate"

# Windows
[team-info を置いた絶対パス]\Remotion\.venv\Scripts\Activate.ps1
```

---

## requirements.txt の更新

現在の venv からパッケージリストを更新する場合:

```bash
"$TEAM_INFO_ROOT/Remotion/.venv/bin/pip" freeze > "$TEAM_INFO_ROOT/setup/requirements.txt"
```
