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

function Invoke-NativeOrThrow {
    param(
        [string]$label,
        [scriptblock]$command
    )

    & $command
    if ($LASTEXITCODE -ne 0) {
        throw "$label に失敗しました。終了コード: $LASTEXITCODE"
    }
}

# ── プロジェクトルート (このスクリプトの親ディレクトリ) ───────────────────
$ScriptDir      = Split-Path -Parent $MyInvocation.MyCommand.Path
$TeamInfoRoot   = Split-Path -Parent $ScriptDir
$VenvDir        = Join-Path $TeamInfoRoot "Remotion\.venv"
$NodeVersion    = "22.17.1"
$PythonVersion  = "3.11.9"
$SecretsDir     = Join-Path $env:USERPROFILE ".secrets"
$CanvaCredentialsFile = Join-Path $SecretsDir "canva_credentials.txt"
$CanvaAuthDir   = Join-Path $TeamInfoRoot "Remotion\scripts\canva_auth"
$DifyRoot       = Join-Path $TeamInfoRoot "docker\dify"
$DifyApiDir     = Join-Path $DifyRoot "api"
$DifyWebDir     = Join-Path $DifyRoot "web"
$DifyWebNvmrc   = Join-Path $DifyWebDir ".nvmrc"
$DifyWebPackage = Join-Path $DifyWebDir "package.json"
$DifySdkDir     = Join-Path $DifyRoot "sdks\nodejs-client"

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
    Invoke-NativeOrThrow "$name の winget install" {
        winget install --id $id --silent --accept-package-agreements --accept-source-agreements
    }
    # PATH 更新
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "$name インストール完了"
}

function Refresh-ProcessPath {
    $machinePath = [System.Environment]::GetEnvironmentVariable("Path","Machine")
    $userPath = [System.Environment]::GetEnvironmentVariable("Path","User")
    $env:Path = "$machinePath;$userPath"
}

function Set-UserEnvVar {
    param($name, $value)
    [System.Environment]::SetEnvironmentVariable($name, $value, "User")
    Set-Item -Path "Env:$name" -Value $value
}

function Add-UserPathEntry {
    param($entry)
    if (-not $entry) {
        return
    }

    $current = [System.Environment]::GetEnvironmentVariable("Path","User")
    $parts = @()
    if ($current) {
        $parts = $current.Split(";") | Where-Object { $_ }
    }

    if ($parts -notcontains $entry) {
        $newPath = @($parts + $entry) -join ";"
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }

    if ($env:Path -notlike "*$entry*") {
        $env:Path = "$entry;$env:Path"
    }
}

function Copy-IfMissing {
    param($source, $target)
    if ((Test-Path $source) -and -not (Test-Path $target)) {
        Copy-Item $source $target
    }
}

function Get-PythonUserScriptsDir {
    param($pythonExe)
    $userBase = (& $pythonExe -c "import site; print(site.USER_BASE)").Trim()
    if (-not $userBase) {
        return $null
    }
    return (Join-Path $userBase "Scripts")
}

function Install-UvUser {
    param($pythonExe)
    $scriptsDir = Get-PythonUserScriptsDir $pythonExe
    Invoke-NativeOrThrow "uv の pip install" {
        & $pythonExe -m pip install --user uv
    }
    if ($scriptsDir) {
        Add-UserPathEntry $scriptsDir
        $uvExe = Join-Path $scriptsDir "uv.exe"
        if (Test-Path $uvExe) {
            return $uvExe
        }
    }
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCommand) {
        return $uvCommand.Source
    }
    return $null
}

function Get-PnpmVersion {
    param($packageJsonPath)
    if (-not (Test-Path $packageJsonPath)) {
        return $null
    }
    try {
        $packageJson = Get-Content $packageJsonPath -Raw | ConvertFrom-Json
    } catch {
        return $null
    }

    $packageManager = $packageJson.packageManager
    if ($packageManager -and $packageManager.StartsWith("pnpm@")) {
        return ($packageManager.Substring(5) -split "\+")[0]
    }

    return $null
}

function Ensure-CanvaCredentialsTemplate {
    New-Item -ItemType Directory -Force -Path $SecretsDir | Out-Null
    if (-not (Test-Path $CanvaCredentialsFile)) {
        Set-Content -Path $CanvaCredentialsFile -Value @(
            "# Canva API credentials"
            "CANVA_CLIENT_ID="
            "CANVA_CLIENT_SECRET="
        )
        Write-Warn "Canva の鍵ファイルを作りました: $CanvaCredentialsFile"
    } else {
        Write-Ok "Canva の鍵ファイルあり: $CanvaCredentialsFile"
    }
}

function Get-NvmExe {
    $candidates = @(
        $env:NVM_HOME,
        [System.Environment]::GetEnvironmentVariable("NVM_HOME","User"),
        [System.Environment]::GetEnvironmentVariable("NVM_HOME","Machine"),
        (Join-Path $env:APPDATA "nvm"),
        (Join-Path $env:LOCALAPPDATA "nvm")
    ) | Where-Object { $_ } | Select-Object -Unique

    foreach ($dir in $candidates) {
        $candidate = Join-Path $dir "nvm.exe"
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $nvmCommand = Get-Command nvm -ErrorAction SilentlyContinue
    if ($nvmCommand) {
        return $nvmCommand.Source
    }

    return $null
}

function Get-NvmSymlink {
    $candidates = @(
        $env:NVM_SYMLINK,
        [System.Environment]::GetEnvironmentVariable("NVM_SYMLINK","User"),
        [System.Environment]::GetEnvironmentVariable("NVM_SYMLINK","Machine"),
        (Join-Path $env:ProgramFiles "nodejs")
    ) | Where-Object { $_ } | Select-Object -Unique

    if ($candidates.Count -gt 0) {
        return $candidates[0]
    }

    return $null
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
    Invoke-NativeOrThrow "pyenv install $PythonVersion" {
        pyenv install $PythonVersion
    }
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
    Invoke-NativeOrThrow "Tesseract の winget install" {
        winget install --id UB-Mannheim.TesseractOCR --silent `
              --accept-package-agreements --accept-source-agreements
    }
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


$Python = Join-Path $VenvDir "Scripts\python.exe"

# pip アップグレード
Invoke-NativeOrThrow "pip の更新" {
    & $Python -m pip install --upgrade pip setuptools wheel -q
}
Write-Ok "pip アップグレード完了"

# ── 7. Python パッケージ ─────────────────────────────────────────────────
Write-Step "7. Python パッケージのインストール"
Write-Info "requirements.txt からインストールします..."
Invoke-NativeOrThrow "requirements.txt の install" {
    & $Python -m pip install -r (Join-Path $ScriptDir "requirements.txt")
}
Write-Ok "requirements.txt インストール完了"

# jax: Windows は CPU 版
Write-Info "jax[cpu] をインストールします..."
try {
    Invoke-NativeOrThrow "jax[cpu] の install" {
        & $Python -m pip install "jax[cpu]==0.4.38"
    }
    Write-Ok "jax インストール完了"
} catch {
    Write-Warn "jax のインストールに失敗しました（スキップ）: $_"
}

# ── 8. uv ────────────────────────────────────────────────────────────────
Write-Step "8. uv"
$UvExe = $null
if (Test-Command uv) {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $UvExe = $uvCommand.Source
    Write-Ok "uv インストール済み"
} else {
    Write-Info "uv を入れます..."
    $UvExe = Install-UvUser $Python311
    if ($UvExe) {
        Write-Ok "uv インストール完了"
    } else {
        Write-Warn "uv の導入に失敗しました。Dify API はあとで確認してください。"
    }
}

# ── 9. TEAM_INFO_ROOT ─────────────────────────────────────────────────────
Write-Step "9. TEAM_INFO_ROOT"
Set-UserEnvVar "TEAM_INFO_ROOT" $TeamInfoRoot
$RuntimeScript = Join-Path $TeamInfoRoot ".agent\skills\common\scripts\team_info_runtime.py"
if (Test-Path $RuntimeScript) {
    try {
        & $Python311 $RuntimeScript setup-local-machine --repo-root $TeamInfoRoot --shell powershell | Out-Null
        Write-Ok "TEAM_INFO_ROOT を保存しました: $TeamInfoRoot"
    } catch {
        Write-Warn "TEAM_INFO_ROOT の保存に失敗しました: $_"
    }
}

# ── 10. nvm-windows + Node.js ─────────────────────────────────────────────
Write-Step "10. nvm-windows + Node.js $NodeVersion"
if (-not (Test-Command nvm)) {
    Write-Info "nvm-windows をインストールします..."
    Invoke-NativeOrThrow "nvm-windows の winget install" {
        winget install --id CoreyButler.NVMforWindows --silent `
              --accept-package-agreements --accept-source-agreements
    }
    Refresh-ProcessPath
    Write-Ok "nvm-windows インストール完了"
} else {
    Write-Ok "nvm-windows インストール済み"
}

$NvmExe = Get-NvmExe
if ($NvmExe) {
    $NvmHome = Split-Path -Parent $NvmExe
    Set-UserEnvVar "NVM_HOME" $NvmHome
    Add-UserPathEntry $NvmHome
    $NodeSymlink = Get-NvmSymlink
    if ($NodeSymlink) {
        Set-UserEnvVar "NVM_SYMLINK" $NodeSymlink
        Add-UserPathEntry $NodeSymlink
    } else {
        $env:Path = "$NvmHome;$env:Path"
    }

    $installedNodes = & $NvmExe list 2>&1
    if ($installedNodes -match $NodeVersion) {
        Write-Ok "Node.js $NodeVersion インストール済み"
    } else {
        Write-Info "Node.js $NodeVersion をインストールします..."
        Invoke-NativeOrThrow "Node.js $NodeVersion の install" {
            & $NvmExe install $NodeVersion
        }
        Write-Ok "Node.js $NodeVersion インストール完了"
    }

    Invoke-NativeOrThrow "Node.js $NodeVersion の use" {
        & $NvmExe use $NodeVersion | Out-Null
    }
    Refresh-ProcessPath
    if ($NodeSymlink) {
        $env:Path = "$NodeSymlink;$env:Path"
    }

    Write-Info "Node.js: $(node --version), npm: $(npm --version)"
} else {
    Write-Warn "nvm を見つけられませんでした。PowerShell を再起動してから再実行してください。"
}

# ── 11. npm パッケージ (Remotion) ────────────────────────────────────────
Write-Step "11. npm パッケージ (Remotion/my-video)"
$RemotionDir = Join-Path $TeamInfoRoot "Remotion\my-video"
if (Test-Command node) {
    if (Test-Path $RemotionDir) {
        Write-Info "npm install を実行します..."
        Push-Location $RemotionDir
        Invoke-NativeOrThrow "Remotion の npm install" {
            npm install
        }
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

# ── 12. MCP サーバー (VOICEVOX) ──────────────────────────────────────────
Write-Step "12. npm パッケージ (mcp-servers/voicevox)"
$VoicevoxMcpDir = Join-Path $TeamInfoRoot "mcp-servers\voicevox"
if ((Test-Path $VoicevoxMcpDir) -and (Test-Command node)) {
    Push-Location $VoicevoxMcpDir
    Invoke-NativeOrThrow "voicevox MCP の npm install" {
        npm install
    }
    try {
        Invoke-NativeOrThrow "voicevox MCP の build" {
            npm run build
        }
        Write-Ok "voicevox MCP build 完了"
    } catch {
        Write-Warn "voicevox MCP build に失敗しました。あとで確認してください。"
    }
    Pop-Location
    Write-Ok "voicevox MCP npm install 完了"
}

# ── 13. npm パッケージ (Canva 補助) ──────────────────────────────────────
Write-Step "13. npm パッケージ (Remotion/scripts/canva_auth)"
if ((Test-Path $CanvaAuthDir) -and (Test-Command node)) {
    Push-Location $CanvaAuthDir
    Invoke-NativeOrThrow "Canva 補助の npm install" {
        npm install
    }
    Pop-Location
    Write-Ok "Canva 補助 npm install 完了"
}

# ── 14. Dify 開発環境 ─────────────────────────────────────────────────────
Write-Step "14. Dify 開発環境"
if (Test-Path $DifyRoot) {
    Copy-IfMissing (Join-Path $DifyApiDir ".env.example") (Join-Path $DifyApiDir ".env")
    Copy-IfMissing (Join-Path $DifyWebDir ".env.example") (Join-Path $DifyWebDir ".env.local")
    Copy-IfMissing (Join-Path $DifyRoot "docker\middleware.env.example") (Join-Path $DifyRoot "docker\middleware.env")

    if ($UvExe -and (Test-Path $DifyApiDir)) {
        Write-Info "Dify API の依存を入れます..."
        try {
            Push-Location $DifyApiDir
            Invoke-NativeOrThrow "Dify API の uv sync" {
                & $UvExe sync --group dev
            }
            Pop-Location
            Write-Ok "Dify API の依存を入れました"
        } catch {
            Pop-Location
            Write-Warn "Dify API の依存で止まりました。あとで uv sync --group dev を見てください。"
        }
    }

    if ((Test-Path $DifyWebNvmrc) -and $NvmExe) {
        $DifyNodeVersion = (Get-Content $DifyWebNvmrc -Raw).Trim()
        if ($DifyNodeVersion) {
            Write-Info "Dify 用の Node.js $DifyNodeVersion を入れます..."
            Invoke-NativeOrThrow "Dify 用 Node.js $DifyNodeVersion の install" {
                & $NvmExe install $DifyNodeVersion | Out-Null
            }
            Invoke-NativeOrThrow "Dify 用 Node.js $DifyNodeVersion の use" {
                & $NvmExe use $DifyNodeVersion | Out-Null
            }
            Refresh-ProcessPath
            if ($NodeSymlink) {
                $env:Path = "$NodeSymlink;$env:Path"
            }

            $PnpmVersion = Get-PnpmVersion $DifyWebPackage
            if (Test-Command corepack) {
                Invoke-NativeOrThrow "corepack enable" {
                    corepack enable
                }
                if ($PnpmVersion) {
                    Invoke-NativeOrThrow "pnpm $PnpmVersion の準備" {
                        corepack prepare "pnpm@$PnpmVersion" --activate
                    }
                }

                if (Test-Path $DifyWebDir) {
                    try {
                        Push-Location $DifyWebDir
                        Invoke-NativeOrThrow "Dify Web の pnpm install" {
                            pnpm install
                        }
                        Pop-Location
                        Write-Ok "Dify Web の依存を入れました"
                    } catch {
                        Pop-Location
                        Write-Warn "Dify Web の依存で止まりました。あとで pnpm install を見てください。"
                    }
                }

                if (Test-Path $DifySdkDir) {
                    try {
                        Push-Location $DifySdkDir
                        Invoke-NativeOrThrow "Dify SDK の pnpm install" {
                            pnpm install
                        }
                        Pop-Location
                        Write-Ok "Dify SDK の依存を入れました"
                    } catch {
                        Pop-Location
                        Write-Warn "Dify SDK の依存で止まりました。あとで pnpm install を見てください。"
                    }
                }
            } else {
                Write-Warn "corepack が見つからないため、Dify の pnpm 準備を飛ばしました。"
            }

            Invoke-NativeOrThrow "Node.js $NodeVersion への復帰" {
                & $NvmExe use $NodeVersion | Out-Null
            }
            Refresh-ProcessPath
            if ($NodeSymlink) {
                $env:Path = "$NodeSymlink;$env:Path"
            }
        }
    }
} else {
    Write-Warn "docker/dify が見つからないため、Dify の準備は飛ばしました。"
}

# ── 15. 秘密ファイルの下準備 ─────────────────────────────────────────────
Write-Step "15. 秘密ファイルの下準備"
Ensure-CanvaCredentialsTemplate
Write-Warn "Canva を使うときは $CanvaCredentialsFile に鍵を書いてください。"
Write-Warn "VOICEVOX 本体アプリは別で入れて起動してください。"

# ── 16. Docker 確認 ───────────────────────────────────────────────────────
Write-Step "16. Docker"
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
Write-Host "  TEAM_INFO_ROOT: $env:TEAM_INFO_ROOT"
Write-Host "  Canva secrets: $CanvaCredentialsFile"
Write-Host ""
Write-Host "次のステップ:"
Write-Host "  ・PowerShell を再起動して PATH を再読み込みしてください"
Write-Host "  ・Claude Code: code `"$TeamInfoRoot`""
Write-Host ""
