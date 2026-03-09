# team-info セットアップ

このフォルダのスクリプトで、macOS/Windows に同じ開発環境を構築できます。

## インストールされるもの

| カテゴリ | 内容 |
|---------|------|
| Python | 3.11 (pyenv 経由) + venv (`Remotion/.venv`) |
| Python パッケージ | Whisper, OpenCV, MediaPipe, JAX, Remotion スクリプト等 |
| Node.js | 22.17.1 (nvm 経由) |
| npm パッケージ | Remotion 4.0.x, React 19, TypeScript 5.9 等 |
| その他 | Git, FFmpeg, Tesseract OCR, Docker (確認のみ) |

---

## macOS

```bash
bash /Users/deguchishouma/team-info/setup/setup_mac.sh
```

- Homebrew → pyenv → Python 3.11 → venv → pip パッケージ → nvm → Node.js → npm の順で自動インストール
- Apple Silicon (M1/M2/M3) は `jax[metal]`、Intel Mac は `jax[cpu]` を自動選択

---

## Windows

PowerShell を**管理者として**開いて実行:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
& "C:\path\to\team-info\setup\setup_windows.ps1"
```

- winget → pyenv-win → Python 3.11 → venv → pip パッケージ → nvm-windows → Node.js → npm の順で自動インストール
- `jax[cpu]` をインストール

> **注意:** nvm-windows のインストール後は PowerShell を再起動してから再実行が必要な場合があります。

---

## Python venv の手動有効化

```bash
# macOS
source /Users/deguchishouma/team-info/Remotion/.venv/bin/activate

# Windows
C:\path\to\team-info\Remotion\.venv\Scripts\Activate.ps1
```

---

## requirements.txt の更新

現在の venv からパッケージリストを更新する場合:

```bash
/Users/deguchishouma/team-info/Remotion/.venv/bin/pip freeze > /Users/deguchishouma/team-info/setup/requirements.txt
```
