# =============================================================================
# team-info セットアップスクリプト (Windows PowerShell)
# =============================================================================
# 使い方（管理者として PowerShell を開いて実行）:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   & "C:\path\to\team-info\setup\setup_windows.ps1"
# =============================================================================

#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# ── カラー出力 ─────────────────────────────────────────────────────────────
function Write-Info    { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Ok      { param($msg) Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }
function Write-Step    { param($msg) Write-Host "`n━━━ $msg ━━━" -ForegroundColor Magenta }

# ── プロジェクトルート (このスクリプトの親ディレクトリ) ───────────────────
$ScriptDir      = Split-Path -Parent $MyInvocation.MyCommand.Path
$TeamInfoRoot   = Split-Path -Parent $ScriptDir
$VenvDir        = Join-Path $TeamInfoRoot "Remotion\.venv"
$NodeVersion    = "22.17.1"
$PythonVersion  = "3.11.9"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Blue
Write-Host "║       team-info セットアップ (Windows)               ║" -ForegroundColor Blue
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Blue
Write-Host ""
Write-Info "プロジェクトルート: $TeamInfoRoot"

# ── ヘルパー: コマンド存在確認 ────────────────────────────────────────────
function Test-Command { param($cmd) return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# ── ヘルパー: winget インストール ─────────────────────────────────────────
function Install-WithWinget {
    param($id, $name)
    Write-Info "$name をインストールします..."
    winget install --id $id --silent --accept-package-agreements --accept-source-agreements
    # PATH 更新
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "$name インストール完了"
}

# ── 1. winget 確認 ────────────────────────────────────────────────────────
Write-Step "1. winget (パッケージマネージャ) 確認"
if (-not (Test-Command winget)) {
    Write-Warn "winget が見つかりません。"
    Write-Warn "→ Microsoft Store から 'アプリ インストーラー' をインストールしてください"
    Write-Warn "→ または https://aka.ms/getwinget から取得してください"
    Write-Err "winget が必要です。インストール後に再実行してください。"
}
Write-Ok "winget: $(winget --version)"

# ── 2. Git ────────────────────────────────────────────────────────────────
Write-Step "2. Git"
if (Test-Command git) {
    Write-Ok "Git インストール済み: $(git --version)"
} else {
    Install-WithWinget "Git.Git" "Git"
}

# ── 3. Python 3.11 ────────────────────────────────────────────────────────
Write-Step "3. Python 3.11"

# pyenv-win インストール
if (-not (Test-Command pyenv)) {
    Write-Info "pyenv-win をインストールします..."
    $pyenvInstallCmd = "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1' -OutFile './install-pyenv-win.ps1'; &'./install-pyenv-win.ps1'"
    Invoke-Expression $pyenvInstallCmd
    # PATH 更新
    $env:PYENV  = "$env:USERPROFILE\.pyenv\pyenv-win"
    $env:Path   = "$env:PYENV\bin;$env:PYENV\shims;$env:Path"
    [System.Environment]::SetEnvironmentVariable("PYENV",  $env:PYENV,  "User")
    [System.Environment]::SetEnvironmentVariable("Path",
        "$env:PYENV\bin;$env:PYENV\shims;" + [System.Environment]::GetEnvironmentVariable("Path","User"),
        "User")
    Write-Ok "pyenv-win インストール完了"
} else {
    Write-Ok "pyenv-win インストール済み"
    $env:PYENV = "$env:USERPROFILE\.pyenv\pyenv-win"
    $env:Path  = "$env:PYENV\bin;$env:PYENV\shims;$env:Path"
}

# Python 3.11 インストール
$pyVersionShort = $PythonVersion.Substring(0, 4)  # "3.11"
if ((pyenv versions 2>&1) -match $PythonVersion) {
    Write-Ok "Python $PythonVersion インストール済み"
} else {
    Write-Info "Python $PythonVersion をインストールします..."
    pyenv install $PythonVersion
    Write-Ok "Python $PythonVersion インストール完了"
}

$Python311 = "$env:USERPROFILE\.pyenv\pyenv-win\versions\$PythonVersion\python.exe"
if (-not (Test-Path $Python311)) {
    # バージョン番号が若干違う場合の fallback
    $Python311 = Get-ChildItem "$env:USERPROFILE\.pyenv\pyenv-win\versions" |
                 Where-Object { $_.Name -like "3.11*" } |
                 Sort-Object Name -Descending |
                 Select-Object -First 1 |
                 ForEach-Object { Join-Path $_.FullName "python.exe" }
}
if (-not (Test-Path $Python311)) { Write-Err "Python $pyVersionShort が見つかりません: $Python311" }
Write-Info "Python: $Python311 ($(& $Python311 --version))"

# ── 4. Tesseract OCR ─────────────────────────────────────────────────────
Write-Step "4. Tesseract OCR (pytesseract 依存)"
if (Test-Command tesseract) {
    Write-Ok "Tesseract インストール済み"
} else {
    Write-Info "Tesseract をインストールします..."
    winget install --id UB-Mannheim.TesseractOCR --silent `
          --accept-package-agreements --accept-source-agreements
    # 標準インストール先を PATH に追加
    $tessPath = "C:\Program Files\Tesseract-OCR"
    if (Test-Path $tessPath) {
        [System.Environment]::SetEnvironmentVariable("Path",
            [System.Environment]::GetEnvironmentVariable("Path","User") + ";$tessPath",
            "User")
        $env:Path += ";$tessPath"
    }
    Write-Ok "Tesseract インストール完了"
}

# ── 5. FFmpeg ─────────────────────────────────────────────────────────────
Write-Step "5. FFmpeg"
if (Test-Command ffmpeg) {
    Write-Ok "FFmpeg インストール済み"
} else {
    Install-WithWinget "Gyan.FFmpeg" "FFmpeg"
}

# ── 6. Python 仮想環境 ────────────────────────────────────────────────────
Write-Step "6. Python 仮想環境 ($VenvDir)"
if (Test-Path $VenvDir) {
    $ans = Read-Host "  既存の venv が見つかりました。再作成しますか? (y/N)"
    if ($ans -match "^[Yy]$") {
        Remove-Item -Recurse -Force $VenvDir
        Write-Info "既存の venv を削除しました"
    }
}

if (-not (Test-Path $VenvDir)) {
    Write-Info "venv を作成します..."
    & $Python311 -m venv $VenvDir
    Write-Ok "venv 作成完了"
}

$Pip    = Join-Path $VenvDir "Scripts\pip.exe"
$Python = Join-Path $VenvDir "Scripts\python.exe"

# pip アップグレード
& $Pip install --upgrade pip setuptools wheel -q
Write-Ok "pip アップグレード完了"

# ── 7. Python パッケージ ─────────────────────────────────────────────────
Write-Step "7. Python パッケージのインストール"
Write-Info "requirements.txt からインストールします..."
& $Pip install -r (Join-Path $ScriptDir "requirements.txt")
Write-Ok "requirements.txt インストール完了"

# jax: Windows は CPU 版
Write-Info "jax[cpu] をインストールします..."
try {
    & $Pip install "jax[cpu]==0.4.38"
    Write-Ok "jax インストール完了"
} catch {
    Write-Warn "jax のインストールに失敗しました（スキップ）: $_"
}

# ── 8. nvm-windows + Node.js ──────────────────────────────────────────────
Write-Step "8. nvm-windows + Node.js $NodeVersion"
$NvmDir = "$env:APPDATA\nvm"
if (-not (Test-Command nvm)) {
    Write-Info "nvm-windows をインストールします..."
    winget install --id CoreyButler.NVMforWindows --silent `
          --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "nvm-windows インストール完了"
    Write-Warn "PowerShell を再起動して nvm コマンドを有効にしてください。"
    Write-Warn "再起動後に以下を実行してください:"
    Write-Warn "  nvm install $NodeVersion"
    Write-Warn "  nvm use $NodeVersion"
} else {
    Write-Ok "nvm-windows インストール済み"
    $installedNodes = nvm list 2>&1
    if ($installedNodes -match $NodeVersion) {
        Write-Ok "Node.js $NodeVersion インストール済み"
    } else {
        Write-Info "Node.js $NodeVersion をインストールします..."
        nvm install $NodeVersion
        Write-Ok "Node.js $NodeVersion インストール完了"
    }
    nvm use $NodeVersion
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Info "Node.js: $(node --version), npm: $(npm --version)"
}

# ── 9. npm パッケージ (Remotion) ─────────────────────────────────────────
Write-Step "9. npm パッケージ (Remotion/my-video)"
$RemotionDir = Join-Path $TeamInfoRoot "Remotion\my-video"
if (Test-Command node) {
    if (Test-Path $RemotionDir) {
        Write-Info "npm install を実行します..."
        Push-Location $RemotionDir
        npm install
        Pop-Location
        Write-Ok "npm install 完了"
    } else {
        Write-Warn "Remotion/my-video が見つかりません: $RemotionDir"
    }
} else {
    Write-Warn "node が見つかりません。PowerShell 再起動後に手動で実行してください:"
    Write-Warn "  cd `"$RemotionDir`""
    Write-Warn "  npm install"
}

# ── 10. MCP サーバー (VOICEVOX) ──────────────────────────────────────────
Write-Step "10. npm パッケージ (mcp-servers/voicevox)"
$VoicevoxMcpDir = Join-Path $TeamInfoRoot "mcp-servers\voicevox"
if ((Test-Path $VoicevoxMcpDir) -and (Test-Command node)) {
    Push-Location $VoicevoxMcpDir
    npm install
    Pop-Location
    Write-Ok "voicevox MCP npm install 完了"
}

# ── 11. Docker 確認 ───────────────────────────────────────────────────────
Write-Step "11. Docker"
if (Test-Command docker) {
    Write-Ok "Docker インストール済み: $(docker --version)"
} else {
    Write-Warn "Docker が見つかりません。"
    Write-Warn "→ https://www.docker.com/products/docker-desktop/ からインストールしてください"
}

# ── 完了 ──────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║       セットアップ完了！                             ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "主要パス:"
Write-Host "  Python venv:   $VenvDir\Scripts\python.exe"
Write-Host "  プロジェクト:  $TeamInfoRoot"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  ・PowerShell を再起動して PATH を再読み込みしてください"
Write-Host "  ・Claude Code: code `"$TeamInfoRoot`""
Write-Host ""
