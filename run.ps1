param(
    [ValidateSet("auto", "current", "n8n", "dify")]
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

function Test-DockerCli {
    try {
        $null = docker --version 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Test-DockerEngine {
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
    try {
        $null = docker compose version 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

function Wait-DockerInstall {
    Notify-User
    Write-Host ""
    Write-Host "Docker Desktop がインストールされていません。"
    Write-Host ""
    Write-Host "以下のページから Docker Desktop をダウンロードしてインストールしてください。"
    Write-Host ""
    Write-Host "https://www.docker.com/ja-jp/get-started/"
    Write-Host ""
    Read-Host "インストールが完了したら Enter を押して続行してください"
}

function Ensure-DockerCli {
    while (-not (Test-DockerCli)) {
        Wait-DockerInstall
    }
    Write-Info "Docker CLI を確認しました: $(docker --version)"
}

function Start-DockerDesktop {
    Write-Info "Docker Desktop を起動します。"
    try {
        docker desktop start | Out-Null
        if ($LASTEXITCODE -eq 0) {
            return
        }
    } catch {
    }

    $exeCandidates = @(
        "C:\Program Files\Docker\Docker\Docker Desktop.exe",
        "C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe"
    )

    foreach ($candidate in $exeCandidates) {
        if (Test-Path $candidate) {
            Start-Process -FilePath $candidate | Out-Null
            return
        }
    }

    Write-WarnLog "Docker Desktop の自動起動に失敗しました。手動で起動してください。"
}

function Wait-DockerEngine {
    $elapsed = 0
    while (-not (Test-DockerEngine)) {
        if ($elapsed -eq 0) {
            Start-DockerDesktop
        }
        if ($elapsed -ge $WaitSeconds) {
            Write-ErrLog "Docker Engine の起動待機がタイムアウトしました。Docker Desktop の状態を確認してください。"
        }
        Write-Info "Waiting for Docker Engine to start..."
        Start-Sleep -Seconds $SleepSeconds
        $elapsed += $SleepSeconds
    }
    Write-Info "Docker Engine が利用可能になりました。"
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
        "n8n" { return (Join-Path $ScriptDir "docker\n8n") }
        "dify" { return (Join-Path $ScriptDir "docker\dify\docker") }
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

    $projectCandidates = @(
        (Join-Path $ScriptDir "docker\n8n"),
        (Join-Path $ScriptDir "docker\dify\docker")
    )

    $validCandidates = @()
    foreach ($candidate in $projectCandidates) {
        if (Get-ComposeFileInDirectory -Directory $candidate) {
            $validCandidates += $candidate
        }
    }

    if ($validCandidates.Count -eq 0) {
        Write-ErrLog "docker compose の対象が見つかりません。compose ファイルがあるディレクトリで実行するか、既知の compose プロジェクトを用意してください。"
    }

    if ($validCandidates.Count -eq 1) {
        return $validCandidates[0]
    }

    Notify-User
    Write-Host "docker compose $Action の対象を選んでください。"
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
        Write-WarnLog "有効な番号を入力してください。"
    }
}

Ensure-DockerCli
if (-not (Test-DockerCompose)) {
    Write-ErrLog "docker compose が利用できません。Docker Desktop の Compose プラグインを確認してください。"
}

if (-not (Test-DockerEngine)) {
    Wait-DockerEngine
} else {
    Write-Info "Docker Engine は既に起動しています。"
}

$ProjectDir = Select-ComposeProject -ProjectName $Project
Write-Info "docker compose $Action を実行します: $ProjectDir"

Push-Location $ProjectDir
try {
    if ($ComposeArgs.Count -gt 0) {
        & docker compose $Action @ComposeArgs
    } else {
        & docker compose $Action
    }
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
