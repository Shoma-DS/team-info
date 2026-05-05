# =============================================================================
# team-info Setup Script (Windows PowerShell - Safe Version)
# =============================================================================

#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# --- Color Output ---
function Write-Info    { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Ok      { param($msg) Write-Host "[OK]    $msg" -ForegroundColor Green }
function Write-Warn    { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Write-Err     { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }
function Write-Step    { param($msg) Write-Host "`n=== $msg ===" -ForegroundColor Magenta }

function Invoke-NativeOrThrow {
    param(
        [string]$label,
        [scriptblock]$command
    )
    & $command
    # winget return codes for "already installed" or "no upgrade available" can be non-zero but non-critical
    if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335189) {
        throw "Failed: $label. Exit code: $LASTEXITCODE"
    }
}

# --- Project Root ---
$ScriptDir      = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptRepoRoot = Split-Path -Parent $ScriptDir
$CurrentDir     = (Get-Location).Path
if ((Test-Path (Join-Path $CurrentDir "AGENTS.md")) -and (Test-Path (Join-Path $CurrentDir "setup\setup_all.cmd"))) {
    $TeamInfoRoot = $CurrentDir
} else {
    $TeamInfoRoot = $ScriptRepoRoot
}
$NodeVersion    = "22.17.1"
$PythonVersion  = "3.11.9"
$CodexNpmPackage = "@openai/codex"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Blue
Write-Host "       team-info Setup (Windows Safe)                 " -ForegroundColor Blue
Write-Host "======================================================" -ForegroundColor Blue
Write-Host ""
Write-Info "Project Root: $TeamInfoRoot"

# --- Helpers ---
function Test-Command { param($cmd) return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

function Install-WithWinget {
    param($id, $name)
    Write-Info "Installing $name..."
    Invoke-NativeOrThrow "winget install $id" {
        winget install --id $id --silent --accept-package-agreements --accept-source-agreements
    }
    Refresh-ProcessPath
    Write-Ok "$name installed."
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
    if (-not $entry) { return }
    $current = [System.Environment]::GetEnvironmentVariable("Path","User")
    $parts = @()
    if ($current) { $parts = $current.Split(";") | Where-Object { $_ } }
    if ($parts -notcontains $entry) {
        $newPath = @($parts + $entry) -join ";"
        [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    }
    if ($env:Path -notlike "*$entry*") { $env:Path = "$entry;$env:Path" }
}

# --- 1. winget Check ---
Write-Step "1. winget check"
if (-not (Test-Command winget)) {
    Write-Err "winget not found. Please install App Installer from Microsoft Store."
}
Write-Ok "winget: $(winget --version)"

# --- 2. Git / rclone ---
Write-Step "2. Git / rclone"
if (Test-Command git) {
    Write-Ok "Git already installed: $(git --version)"
} else {
    Install-WithWinget "Git.Git" "Git"
}

if (Test-Command rclone) {
    Write-Ok "rclone already installed"
} else {
    Install-WithWinget "Rclone.Rclone" "rclone"
}

# --- 3. GitHub CLI ---
Write-Step "3. GitHub CLI"
if (Test-Command gh) {
    Write-Ok "gh already installed"
} else {
    Install-WithWinget "GitHub.cli" "GitHub CLI"
}

# --- 4. Python (pyenv-win) ---
Write-Step "4. Python $PythonVersion"
if (-not (Test-Command pyenv)) {
    Write-Info "Installing pyenv-win..."
    $pyenvInstallCmd = "Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1' -OutFile './install-pyenv-win.ps1'; &'./install-pyenv-win.ps1'"
    Invoke-Expression $pyenvInstallCmd
    $env:PYENV  = "$env:USERPROFILE\.pyenv\pyenv-win"
    $env:Path   = "$env:PYENV\bin;$env:PYENV\shims;$env:Path"
    [System.Environment]::SetEnvironmentVariable("PYENV", $env:PYENV, "User")
    Write-Ok "pyenv-win installed."
} else {
    Write-Ok "pyenv-win already installed"
}

# --- 5. TEAM_INFO_ROOT ---
Write-Step "5. TEAM_INFO_ROOT"
Set-UserEnvVar "TEAM_INFO_ROOT" $TeamInfoRoot
Write-Ok "TEAM_INFO_ROOT set to $TeamInfoRoot"

# --- 6. Node.js (nvm-windows) ---
Write-Step "6. Node.js $NodeVersion"
if (-not (Test-Command nvm)) {
    Install-WithWinget "CoreyButler.NVMforWindows" "nvm-windows"
}
Write-Ok "nvm-windows check done."

# --- 7. PowerShell Aliases ---
Write-Step "7. PowerShell Aliases (x-post / remotion)"
$profileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($profileContent -notlike "*function x-post*") {
    Add-Content -Path $PROFILE -Value ""
    Add-Content -Path $PROFILE -Value "# チームツール起動エイリアス (team-info setup により追加)"
    Add-Content -Path $PROFILE -Value "function setup { & `"`$env:TEAM_INFO_ROOT\setup\setup_windows_safe.ps1`" }"
    Add-Content -Path $PROFILE -Value "function x-post { bash `"`$env:TEAM_INFO_ROOT/.agent/skills/x-post-writer/scripts/start_preview.sh`" }"
    Add-Content -Path $PROFILE -Value "function remotion { npm --prefix `"`$env:TEAM_INFO_ROOT/Remotion/my-video`" run dev }"
    Write-Ok "PowerShell aliases added: x-post, remotion"
} else {
    Write-Ok "PowerShell aliases already set"
}

# --- Final ---
Write-Step "Final"
Write-Ok "Core setup components installed or verified."
Write-Info "Please restart your terminal to refresh environment variables."
Write-Info "Then run run.ps1 to start services."
