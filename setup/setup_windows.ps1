# =============================================================================
# team-info setup script (Windows PowerShell)
# =============================================================================
# Usage:
#   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
#   & "C:\path\to\team-info\setup\setup_windows.ps1"
# =============================================================================

#Requires -Version 5.1
$ErrorActionPreference = "Stop"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {
    # Keep setup running even on hosts where console encoding cannot be changed.
}

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
    if ($LASTEXITCODE -ne 0) {
        throw "$label failed. Exit code: $LASTEXITCODE"
    }
}

# Project root: prefer the current directory when it is the repo root.
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
$FreebuffNpmPackage = "freebuff"
$NpmUserPrefix = Join-Path $env:USERPROFILE ".local\npm"

Write-Host ""
Write-Host "======================================================" -ForegroundColor Blue
Write-Host "       team-info setup (Windows)" -ForegroundColor Blue
Write-Host "======================================================" -ForegroundColor Blue
Write-Host ""
Write-Info "Project root: $TeamInfoRoot"

# Helper: command lookup.
function Test-Command { param($cmd) return [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

# Helper: winget install.
function Install-WithWinget {
    param($id, $name)
    Write-Info "Installing $name..."
    Invoke-NativeOrThrow "$name winget install" {
        winget install --id $id --silent --accept-package-agreements --accept-source-agreements
    }
    # Refresh PATH.
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + `
                [System.Environment]::GetEnvironmentVariable("Path","User")
    Write-Ok "$name installed"
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

function Test-DirectoryWritable {
    param($path)
    if (-not $path) {
        return $false
    }

    try {
        if (-not (Test-Path $path)) {
            New-Item -ItemType Directory -Force -Path $path | Out-Null
        }

        $testPath = Join-Path $path ".team-info-write-test"
        [System.IO.File]::WriteAllText($testPath, "")
        Remove-Item -Force $testPath
        return $true
    } catch {
        return $false
    }
}

function Use-UserNpmPrefixIfNeeded {
    $globalRoot = (& npm root -g 2>$null | Select-Object -First 1)
    if ($globalRoot -and (Test-DirectoryWritable $globalRoot)) {
        return
    }

    New-Item -ItemType Directory -Force -Path $NpmUserPrefix | Out-Null
    $env:NPM_CONFIG_PREFIX = $NpmUserPrefix
    Add-UserPathEntry $NpmUserPrefix
    Write-Warn "npm global install target is not writable: $(if ($globalRoot) { $globalRoot } else { 'unknown' })"
    Write-Info "Using user npm prefix: $NpmUserPrefix"
}

function Install-NpmCli {
    param(
        [string]$label,
        [string]$packageName,
        [string]$commandName
    )

    if (-not (Test-Command npm)) {
        Write-Warn "npm was not found. Restart PowerShell, then run:"
        Write-Warn "  `$env:NPM_CONFIG_PREFIX = `"$NpmUserPrefix`"; npm install -g $packageName"
        return
    }

    if (Test-Command $commandName) {
        Write-Info "Updating $label..."
    } else {
        Write-Info "Installing $label globally..."
    }

    try {
        Use-UserNpmPrefixIfNeeded
        Invoke-NativeOrThrow "$label npm install -g" {
            npm install -g $packageName
        }
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($command) {
            Write-Ok "$label installed: $($command.Source)"
        } else {
            Write-Ok "$label installed"
        }
    } catch {
        Write-Warn "$label install failed. Run this later:"
        Write-Warn "  `$env:NPM_CONFIG_PREFIX = `"$NpmUserPrefix`"; npm install -g $packageName"
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
    Invoke-NativeOrThrow "uv pip install" {
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

function Resolve-NodeAndNpmCommand {
    param(
        [string]$nvmExe,
        [string]$nodeVersion,
        [string]$nodeSymlink
    )

    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue

    if ($nodeCommand -and $npmCommand) {
        return [PSCustomObject]@{
            Node = $nodeCommand.Source
            Npm = $npmCommand.Source
        }
    }

    $candidates = @()
    if ($nodeSymlink) {
        $candidates += $nodeSymlink
    }

    if ($nvmExe) {
        $nvmHome = Split-Path -Parent $nvmExe
        $normalizedNodeVersion = $nodeVersion
        if ($normalizedNodeVersion -notmatch '^v') {
            $normalizedNodeVersion = "v$normalizedNodeVersion"
        }
        $candidates += (Join-Path $nvmHome $normalizedNodeVersion)
    }

    foreach ($dir in ($candidates | Where-Object { $_ } | Select-Object -Unique)) {
        $nodeExe = Join-Path $dir "node.exe"
        $npmCmd = Join-Path $dir "npm.cmd"
        if ((Test-Path $nodeExe) -and (Test-Path $npmCmd)) {
            if ($env:Path -notlike "*$dir*") {
                $env:Path = "$dir;$env:Path"
            }
            return [PSCustomObject]@{
                Node = $nodeExe
                Npm = $npmCmd
            }
        }
    }

    return $null
}

# 1. winget check
Write-Step "1. winget check"
if (-not (Test-Command winget)) {
    Write-Warn "winget was not found."
    Write-Warn "Install 'App Installer' from Microsoft Store."
    Write-Warn "Or get winget from https://aka.ms/getwinget"
    Write-Err "winget is required. Install it, then rerun setup."
}
Write-Ok "winget: $(winget --version)"

# 1b. PowerShell 7 and UTF-8 defaults
Write-Step "1b. PowerShell 7 and UTF-8 defaults"
Set-UserEnvVar "PYTHONUTF8" "1"
Set-UserEnvVar "PYTHONIOENCODING" "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$PSDefaultParameterValues["*:Encoding"] = "utf8"

if (Test-Command pwsh) {
    Write-Ok "PowerShell 7 installed: $((& pwsh --version 2>$null | Select-Object -First 1))"
} else {
    Install-WithWinget "Microsoft.PowerShell" "PowerShell 7"
    Refresh-ProcessPath
    if (Test-Command pwsh) {
        Write-Ok "PowerShell 7 installed: $((& pwsh --version 2>$null | Select-Object -First 1))"
    } else {
        Write-Warn "PowerShell 7 was installed but pwsh is not on PATH yet. Restart PowerShell after setup."
    }
}
Write-Ok "UTF-8 env set: PYTHONUTF8=1, PYTHONIOENCODING=utf-8"

# 2. Git / rclone
Write-Step "2. Git / rclone"
if (Test-Command git) {
    Write-Ok "Git installed: $(git --version)"
} else {
    Install-WithWinget "Git.Git" "Git"
}

if (Test-Command rclone) {
    Write-Ok "rclone installed: $((& rclone version | Select-Object -First 1))"
} else {
    Install-WithWinget "Rclone.Rclone" "rclone"
}

try {
    Invoke-NativeOrThrow "git lfs install" {
        git lfs install --skip-repo | Out-Null
    }
    Write-Ok "git lfs initialized"
} catch {
    Write-Warn "git lfs init failed. Run manually if needed: git lfs install --skip-repo"
}

# 3. GitHub access and repo connection
Write-Step "3. GitHub access and repo connection"
if (Test-Command gh) {
    Write-Ok "GitHub CLI (gh) installed: $(gh --version | Select-Object -First 1)"
} else {
    Install-WithWinget "GitHub.cli" "GitHub CLI (gh)"
}

Write-Warn "The GitHub invite must already be accepted."
$confirmed = Read-Host "  Have you accepted the GitHub invite? Enter y if yes [y/N]"
if ($confirmed -notmatch "^[Yy]$") {
    Write-Err "Accept the invite first. Ask sho if unclear."
}

$authStatus = gh auth status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Ok "GitHub CLI (gh) authenticated"
} else {
    Write-Info "Starting GitHub CLI (gh) auth. Log in from the browser..."
    & gh auth login --web -h github.com -p https -w
    Write-Ok "GitHub CLI (gh) auth complete"
}

Write-Info "Setting remote repository URL..."
& git remote set-url origin https://github.com/Shoma-DS/team-info.git
Write-Ok "Remote URL set: https://github.com/Shoma-DS/team-info.git"

# 4. Python
Write-Step "4. Python $PythonVersion"

# Install pyenv-win.
if (-not (Test-Command pyenv)) {
    Write-Info "Installing pyenv-win..."
    $PyenvInstallScript = Join-Path $env:TEMP "team-info-pyenv-win-install.ps1"
    Invoke-WebRequest -UseBasicParsing `
        -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" `
        -OutFile $PyenvInstallScript
    & $PyenvInstallScript
    # Refresh PATH.
    $env:PYENV  = "$env:USERPROFILE\.pyenv\pyenv-win"
    $env:Path   = "$env:PYENV\bin;$env:PYENV\shims;$env:Path"
    [System.Environment]::SetEnvironmentVariable("PYENV",  $env:PYENV,  "User")
    [System.Environment]::SetEnvironmentVariable("Path",
        "$env:PYENV\bin;$env:PYENV\shims;" + [System.Environment]::GetEnvironmentVariable("Path","User"),
        "User")
    Write-Ok "pyenv-win installed"
} else {
    Write-Ok "pyenv-win installed"
    $env:PYENV = "$env:USERPROFILE\.pyenv\pyenv-win"
    $env:Path  = "$env:PYENV\bin;$env:PYENV\shims;$env:Path"
}

# Install Python.
if ((pyenv versions 2>&1) -match $PythonVersion) {
    Write-Ok "Python $PythonVersion installed"
} else {
    Write-Info "Installing Python $PythonVersion..."
    Invoke-NativeOrThrow "pyenv install $PythonVersion" {
        pyenv install $PythonVersion
    }
    Write-Ok "Python $PythonVersion installed"
}

$Python311 = "$env:USERPROFILE\.pyenv\pyenv-win\versions\$PythonVersion\python.exe"
if (-not (Test-Path $Python311)) { Write-Err "Python $PythonVersion was not found: $Python311" }
Write-Info "Python: $Python311 ($(& $Python311 --version))"

# 5. Python runtime policy
Write-Step "5. Python runtime policy"
Write-Ok "Python 3.11 base is ready"
Write-Warn "Remotion / Docker runtime and Python packages are prepared lazily by the relevant skill."

# 6. uv
Write-Step "6. uv"
$UvExe = $null
if (Test-Command uv) {
    $uvCommand = Get-Command uv -ErrorAction SilentlyContinue
    $UvExe = $uvCommand.Source
    Write-Ok "uv installed"
} else {
    Write-Info "Installing uv..."
    $UvExe = Install-UvUser $Python311
    if ($UvExe) {
        Write-Ok "uv installed"
    } else {
        Write-Warn "uv install failed. Check Python helper tools later."
    }
}

# 7. TEAM_INFO_ROOT
Write-Step "7. TEAM_INFO_ROOT"
Set-UserEnvVar "TEAM_INFO_ROOT" $TeamInfoRoot
$RuntimeScript = Join-Path $TeamInfoRoot ".agent\skills\common\scripts\team_info_runtime.py"
if (Test-Path $RuntimeScript) {
    try {
        & $Python311 $RuntimeScript setup-local-machine --repo-root $TeamInfoRoot --shell powershell | Out-Null
        Write-Ok "TEAM_INFO_ROOT saved: $TeamInfoRoot"
    } catch {
        Write-Warn "TEAM_INFO_ROOT save failed: $_"
    }
}

$AliasScript = Join-Path $TeamInfoRoot ".agent\skills\common\scripts\register_aliases.py"
if (Test-Path $AliasScript) {
    try {
        & $Python311 $AliasScript --root $TeamInfoRoot | Out-Null
        Write-Ok "Registered PowerShell commands: setup / x-post / remotion / renda"
    } catch {
        Write-Warn "PowerShell command registration failed: $_"
    }
}

# 8. nvm-windows + Node.js
Write-Step "8. nvm-windows + Node.js $NodeVersion"
if (-not (Test-Command nvm)) {
    Write-Info "Installing nvm-windows..."
    Invoke-NativeOrThrow "nvm-windows winget install" {
        winget install --id CoreyButler.NVMforWindows --silent `
              --accept-package-agreements --accept-source-agreements
    }
    Refresh-ProcessPath
    Write-Ok "nvm-windows installed"
} else {
    Write-Ok "nvm-windows installed"
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
        Write-Ok "Node.js $NodeVersion installed"
    } else {
        Write-Info "Installing Node.js $NodeVersion..."
        Invoke-NativeOrThrow "Node.js $NodeVersion install" {
            & $NvmExe install $NodeVersion
        }
        Write-Ok "Node.js $NodeVersion installed"
    }

    Invoke-NativeOrThrow "Node.js $NodeVersion use" {
        & $NvmExe use $NodeVersion | Out-Null
    }
    Refresh-ProcessPath
    if ($NodeSymlink) {
        $env:Path = "$NodeSymlink;$env:Path"
    }

    $nodeAndNpm = Resolve-NodeAndNpmCommand -nvmExe $NvmExe -nodeVersion $NodeVersion -nodeSymlink $NodeSymlink
    if ($nodeAndNpm) {
        $nodeVersionText = (& $nodeAndNpm.Node --version 2>$null | Select-Object -First 1)
        $npmVersionText = (& $nodeAndNpm.Npm --version 2>$null | Select-Object -First 1)
        if ($nodeVersionText -and $npmVersionText) {
            Write-Info "Node.js: $nodeVersionText, npm: $npmVersionText"
        } else {
            Write-Warn "Node/npm version check failed. Restart PowerShell and check again."
        }
    } else {
        Write-Warn "node/npm was not found. Restart PowerShell and rerun setup."
    }
} else {
    Write-Warn "nvm was not found. Restart PowerShell and rerun setup."
}

# 9. Codex CLI
Write-Step "9. Codex CLI"
Install-NpmCli "Codex CLI" $CodexNpmPackage "codex"

# 10. Freebuff CLI
Write-Step "10. Freebuff CLI (free AI agent)"
Install-NpmCli "Freebuff CLI" $FreebuffNpmPackage "freebuff"

# 11. Git hooks
Write-Step "11. Git hooks"
try {
    git -C $TeamInfoRoot config core.hooksPath .githooks
    Write-Ok "core.hooksPath set to .githooks"
} catch {
    Write-Warn "core.hooksPath setup failed. Run manually: git config core.hooksPath .githooks"
}

# 12. Lazy setup notice
Write-Step "12. Lazy setup notice"
Write-Warn "These are not installed by core setup. They are prepared when the relevant skill first runs."
Write-Warn "  - Remotion / VOICEVOX / Docker runtime"
Write-Warn "  - Extra dev dependencies such as Canva helpers"
Write-Warn "  - Agent Reach / OpenClaw / Obsidian / Claudian"
Write-Warn "  - shared-agent-assets sync"
Write-Warn "  - Node 24 workspace dependencies for clone-website"

# 13. Docker optional
Write-Step "13. Docker optional"
if (Test-Command docker) {
    Write-Ok "Docker installed: $(docker --version)"
    Write-Warn "Docker image build / pull is heavy, so it runs on first relevant skill use."
} else {
    Write-Warn "Docker was not found."
    Write-Warn "Docker Desktop is optional. Prepare WSL2 Docker Engine + Compose v2 when needed."
    Write-Warn "& `"$env:TEAM_INFO_ROOT\setup\setup_wsl_docker_engine.ps1`" -Distro Ubuntu"
}

# 14. Verify setup
$VerifyStatus = 0
Write-Step "14. Verify setup"
$VerifyScript = Join-Path $ScriptDir "verify_setup.py"
if (Test-Path $VerifyScript) {
    try {
        & $Python311 $VerifyScript --repo-root $TeamInfoRoot
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Setup verification complete"
        } else {
            $VerifyStatus = $LASTEXITCODE
            Write-Warn "Setup verification found missing items. Check the log and fill gaps."
        }
    } catch {
        $VerifyStatus = 1
        Write-Warn "Setup verification failed: $_"
    }
} else {
    $VerifyStatus = 1
    Write-Warn "Verification script was not found: $VerifyScript"
}

# Done.
Write-Host ""
if ($VerifyStatus -eq 0) {
    Write-Host "======================================================" -ForegroundColor Green
    Write-Host "       Setup completed" -ForegroundColor Green
    Write-Host "======================================================" -ForegroundColor Green
} else {
    Write-Host "======================================================" -ForegroundColor Yellow
    Write-Host "       Setup finished with warnings" -ForegroundColor Yellow
    Write-Host "======================================================" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Key paths:"
Write-Host "  Python:        $Python311"
Write-Host "  PowerShell 7:  $(if (Get-Command pwsh -ErrorAction SilentlyContinue) { (Get-Command pwsh -ErrorAction SilentlyContinue | ForEach-Object Source | Select-Object -First 1) } else { 'restart PowerShell and check again' })"
Write-Host "  Node.js:       $(if (Get-Command node -ErrorAction SilentlyContinue) { (Get-Command node -ErrorAction SilentlyContinue | ForEach-Object Source | Select-Object -First 1) } else { 'restart PowerShell and check again' })"
Write-Host "  Codex CLI:     $(if (Get-Command codex -ErrorAction SilentlyContinue) { (Get-Command codex -ErrorAction SilentlyContinue | ForEach-Object Source | Select-Object -First 1) } else { 'rerun setup or install manually' })"
Write-Host "  Freebuff CLI:  $(if (Get-Command freebuff -ErrorAction SilentlyContinue) { (Get-Command freebuff -ErrorAction SilentlyContinue | ForEach-Object Source | Select-Object -First 1) } else { 'rerun setup or install manually' })"
Write-Host "  Project:       $TeamInfoRoot"
Write-Host "  TEAM_INFO_ROOT: $env:TEAM_INFO_ROOT"
Write-Host "  Verify result: $(if ($VerifyStatus -eq 0) { 'passed' } else { 'needs review' })"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  - Restart PowerShell to reload PATH and setup / x-post / remotion / renda."
Write-Host "  - Use pwsh for Windows work when Japanese or UTF-8 text is involved."
Write-Host "  - To use a free AI agent, run freebuff in the repo."
Write-Host "  - Remotion prepares Docker runtime on first relevant use."
Write-Host "  - Agent Reach bootstraps on first use."
Write-Host "  - Run /claudian when Claudian is needed."
Write-Host "  - Claude Code: code `"$TeamInfoRoot`""
Write-Host ""

exit $VerifyStatus
