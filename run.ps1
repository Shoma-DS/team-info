param(
    [ValidateSet("auto", "current")]
    [string]$Project = "auto",

    [ValidateSet("up", "down", "stop", "start", "restart", "ps")]
    [string]$Action = "up",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ComposeArgs
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WaitSeconds = if ($env:DOCKER_ENGINE_WAIT_SECONDS) { [int]$env:DOCKER_ENGINE_WAIT_SECONDS } else { 180 }
$SleepSeconds = if ($env:DOCKER_ENGINE_POLL_SECONDS) { [int]$env:DOCKER_ENGINE_POLL_SECONDS } else { 2 }
$script:DockerMode = $null
$script:WslDistro = $null
$script:DockerComposeCommand = $null

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-WarnLog {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-ErrLog {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
    exit 1
}

function Notify-User {
    [console]::beep(800, 200)
}

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-WslDistroName {
    if ($env:TEAM_INFO_WSL_DISTRO) {
        return $env:TEAM_INFO_WSL_DISTRO
    }

    if (-not (Test-CommandExists "wsl.exe")) {
        return $null
    }

    try {
        $distros = @(wsl.exe -l -q 2>$null) |
            ForEach-Object { ($_ -replace "`0", "").Trim() } |
            Where-Object { $_ -and $_ -notin @("docker-desktop", "docker-desktop-data") }
        if ($distros.Count -gt 0) {
            return $distros[0]
        }
    } catch {
    }

    return $null
}

function Get-WslBaseArgs {
    if (-not $script:WslDistro) {
        $script:WslDistro = Get-WslDistroName
    }

    if ($script:WslDistro) {
        return @("-d", $script:WslDistro)
    }

    return @()
}

function Invoke-WslShell {
    param([string]$Command)
    $args = @(Get-WslBaseArgs) + @("-e", "sh", "-lc", $Command)
    & wsl.exe @args
}

function Invoke-WslCommand {
    param([string[]]$Arguments)
    $args = @(Get-WslBaseArgs) + @("-e") + $Arguments
    & wsl.exe @args
}

function ConvertTo-WslPath {
    param([string]$WindowsPath)
    $converted = Invoke-WslCommand -Arguments @("wslpath", "-a", $WindowsPath) 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $converted) {
        Write-ErrLog "WSL path への変換に失敗しました: $WindowsPath"
    }
    return ($converted | Select-Object -First 1).Trim()
}

function Test-DockerCli {
    try {
        $null = docker --version 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-WslDockerCli {
    if (-not (Test-CommandExists "wsl.exe")) {
        return $false
    }
    $candidateDistro = Get-WslDistroName
    if (-not $candidateDistro) {
        return $false
    }
    $script:WslDistro = $candidateDistro
    try {
        $null = Invoke-WslShell "command -v docker >/dev/null 2>&1 && docker --version >/dev/null 2>&1"
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-WslDockerEngine {
    try {
        $null = Invoke-WslShell "docker info >/dev/null 2>&1 || docker ps >/dev/null 2>&1"
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-WslDockerCompose {
    try {
        $null = Invoke-WslShell "docker compose version >/dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            $script:DockerComposeCommand = @("docker", "compose")
            return $true
        }
        $null = Invoke-WslShell "command -v docker-compose >/dev/null 2>&1 && docker-compose version >/dev/null 2>&1"
        if ($LASTEXITCODE -eq 0) {
            $script:DockerComposeCommand = @("docker-compose")
            return $true
        }
        return $false
    } catch {
        return $false
    }
}

function Test-DockerEngine {
    if ($script:DockerMode -eq "wsl") {
        return Test-WslDockerEngine
    }

    try {
        $null = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        $null = docker ps 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-DockerCompose {
    if ($script:DockerMode -eq "wsl") {
        return Test-WslDockerCompose
    }

    try {
        $null = docker compose version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $script:DockerComposeCommand = @("docker", "compose")
            return $true
        }
        if (Test-CommandExists "docker-compose") {
            $null = docker-compose version 2>$null
            if ($LASTEXITCODE -eq 0) {
                $script:DockerComposeCommand = @("docker-compose")
                return $true
            }
        }
        return $false
    } catch {
        return $false
    }
}

function Wait-DockerInstall {
    Notify-User
    Write-Host ""
    Write-Host "Docker CLI was not found. For Docker Desktop-free usage, install Docker Engine inside WSL2 Ubuntu."
    Write-Host ""
    Write-Host "Make sure docker and docker compose work inside Ubuntu. Set TEAM_INFO_WSL_DISTRO if you need a specific distro."
    Write-Host ""
    Write-Host "Check commands:"
    Write-Host "  wsl -d Ubuntu -- docker version"
    Write-Host "  wsl -d Ubuntu -- docker compose version"
    Write-Host ""
    Read-Host "Press Enter after the WSL Docker Engine setup is complete"
}

function Ensure-DockerCli {
    while ($true) {
        if (Test-DockerCli) {
            $script:DockerMode = "native"
            if (Test-DockerEngine) {
                Write-Info "Docker CLI detected: $(docker --version)"
                return
            }
            if (Test-WslDockerCli) {
                $script:DockerMode = "wsl"
                $distroLabel = if ($script:WslDistro) { $script:WslDistro } else { "default" }
                Write-Info "WSL Docker CLI detected: distro=$distroLabel"
                return
            }
            Write-Info "Docker CLI detected: $(docker --version)"
            return
        }
        if (Test-WslDockerCli) {
            $script:DockerMode = "wsl"
            $distroLabel = if ($script:WslDistro) { $script:WslDistro } else { "default" }
            Write-Info "WSL Docker CLI detected: distro=$distroLabel"
            return
        }
        Wait-DockerInstall
    }
}

function Start-DockerEngine {
    if ($script:DockerMode -eq "wsl") {
        Write-Info "Trying to start Docker Engine inside WSL."
        $null = Invoke-WslShell "if command -v systemctl >/dev/null 2>&1; then sudo systemctl start docker; else sudo service docker start; fi" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-WarnLog "Could not start Docker Engine inside WSL automatically. Run 'sudo systemctl start docker' or 'sudo service docker start' in Ubuntu."
        }
        return
    }

    if ($env:TEAM_INFO_DOCKER_START_COMMAND) {
        Write-Info "Running TEAM_INFO_DOCKER_START_COMMAND."
        cmd.exe /c $env:TEAM_INFO_DOCKER_START_COMMAND | Out-Null
        return
    }

    Write-WarnLog "Could not start Docker Engine automatically. Start Docker Engine manually, or run setup\setup_wsl_docker_engine.ps1 and use WSL Docker Engine."
}

function Wait-DockerEngine {
    $elapsed = 0
    while (-not (Test-DockerEngine)) {
        if ($elapsed -eq 0) {
            Start-DockerEngine
        }
        if ($elapsed -ge $WaitSeconds) {
            if ($script:DockerMode -eq "wsl") {
                Write-ErrLog "Timed out waiting for Docker Engine. Check the docker service inside WSL."
            }
            Write-ErrLog "Timed out waiting for Docker Engine. Check Docker Engine status."
        }
        Write-Info "Waiting for Docker Engine to start..."
        Start-Sleep -Seconds $SleepSeconds
        $elapsed += $SleepSeconds
    }
    Write-Info "Docker Engine is ready."
}

function Get-ComposeFileInDirectory {
    param([string]$Directory)

    $candidates = @("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")
    foreach ($name in $candidates) {
        $path = Join-Path $Directory $name
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

function Resolve-ProjectDirectory {
    param([string]$ProjectName)

    switch ($ProjectName) {
        "current" { return (Get-Location).Path }
        default { return $null }
    }
}

function Select-ComposeProject {
    param([string]$ProjectName = "auto")

    if ($ProjectName -ne "auto") {
        $explicitDir = Resolve-ProjectDirectory -ProjectName $ProjectName
        if (-not $explicitDir) {
            Write-ErrLog "不明な project です: $ProjectName"
        }
        if (Get-ComposeFileInDirectory -Directory $explicitDir) {
            return $explicitDir
        }
        Write-ErrLog "compose ファイルが見つかりません: $explicitDir"
    }

    $currentCompose = Get-ComposeFileInDirectory -Directory (Get-Location).Path
    if ($currentCompose) {
        return (Get-Location).Path
    }

    $projectCandidates = @()

    $validCandidates = @()
    foreach ($candidate in $projectCandidates) {
        if (Get-ComposeFileInDirectory -Directory $candidate) {
            $validCandidates += $candidate
        }
    }

    if ($validCandidates.Count -eq 0) {
        Write-ErrLog "No docker compose target found. Run from a compose directory or use -Project current."
    }

    if ($validCandidates.Count -eq 1) {
        return $validCandidates[0]
    }

    Notify-User
    Write-Host "Select docker compose target for action: $Action"
    for ($i = 0; $i -lt $validCandidates.Count; $i++) {
        $relative = Resolve-Path -Relative $validCandidates[$i]
        Write-Host ("  {0}. {1}" -f ($i + 1), $relative)
    }

    while ($true) {
        $selection = Read-Host "番号を入力してください"
        $index = 0
        if ([int]::TryParse($selection, [ref]$index) -and $index -ge 1 -and $index -le $validCandidates.Count) {
            return $validCandidates[$index - 1]
        }
        Write-WarnLog "Enter a valid number."
    }
}

Ensure-DockerCli
if (-not (Test-DockerCompose)) {
    Write-ErrLog "docker compose is not available. Install Docker Compose v2 in Windows or WSL."
}

if (-not (Test-DockerEngine)) {
    Wait-DockerEngine
} else {
    Write-Info "Docker Engine is already running."
}

$ProjectDir = Select-ComposeProject -ProjectName $Project
Write-Info "docker compose $Action を実行します: $ProjectDir"

if ($script:DockerMode -eq "wsl") {
    $WslProjectDir = ConvertTo-WslPath -WindowsPath $ProjectDir
    Write-Info "WSL path: $WslProjectDir"
    $wslArgs = @(Get-WslBaseArgs) + @("--cd", $WslProjectDir, "-e") + $script:DockerComposeCommand + @($Action) + $ComposeArgs
    & wsl.exe @wslArgs
    exit $LASTEXITCODE
} else {
    Push-Location $ProjectDir
    try {
        $ComposeExecutable = $script:DockerComposeCommand[0]
        $ComposePrefixArgs = @($script:DockerComposeCommand | Select-Object -Skip 1)
        if ($ComposeArgs.Count -gt 0) {
            & $ComposeExecutable @ComposePrefixArgs $Action @ComposeArgs
        } else {
            & $ComposeExecutable @ComposePrefixArgs $Action
        }
        exit $LASTEXITCODE
    } finally {
        Pop-Location
    }
}
