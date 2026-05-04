# This script prepares Docker Engine inside a WSL2 Linux distro for team-info.
# It installs or selects a WSL distro, installs Docker Engine + Compose v2 via
# Docker's official apt repository, and records TEAM_INFO_WSL_DISTRO for
# PowerShell-based launchers such as run.ps1.

#Requires -Version 5.1
param(
    [string]$Distro = "Ubuntu",
    [string]$UbuntuMirror = "http://jp.archive.ubuntu.com/ubuntu",
    [switch]$SkipDistroInstall,
    [switch]$SkipDockerInstall
)

$ErrorActionPreference = "Stop"

function Write-Info { param([string]$Message) Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Ok { param([string]$Message) Write-Host "[OK] $Message" -ForegroundColor Green }
function Write-WarnLog { param([string]$Message) Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-ErrLog { param([string]$Message) Write-Host "[ERROR] $Message" -ForegroundColor Red; exit 1 }

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-WslDistros {
    @(wsl.exe -l -q 2>$null) |
        ForEach-Object { ($_ -replace "`0", "").Trim() } |
        Where-Object { $_ }
}

function Test-WslDistro {
    param([string]$Name)
    return [bool]((Get-WslDistros) | Where-Object { $_ -eq $Name })
}

function Invoke-WslShell {
    param(
        [string]$DistroName,
        [string]$Command,
        [string]$StepName = "WSL command",
        [int]$StepIndex = 1,
        [int]$TotalSteps = 1
    )
    $tempScript = Join-Path ([System.IO.Path]::GetTempPath()) ("team-info-wsl-docker-{0}.sh" -f ([guid]::NewGuid().ToString("N")))
    $stdoutPath = Join-Path ([System.IO.Path]::GetTempPath()) ("team-info-wsl-docker-{0}.out" -f ([guid]::NewGuid().ToString("N")))
    $stderrPath = Join-Path ([System.IO.Path]::GetTempPath()) ("team-info-wsl-docker-{0}.err" -f ([guid]::NewGuid().ToString("N")))
    try {
        $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText($tempScript, $Command, $utf8NoBom)

        $wslPathOutput = & wsl.exe -d $DistroName -e wslpath -a $tempScript
        $wslPathExitCode = $LASTEXITCODE
        $wslScriptPath = ($wslPathOutput | Select-Object -First 1).Trim()
        if ($wslPathExitCode -ne 0 -or -not $wslScriptPath) {
            throw "Failed to convert temp script path for WSL."
        }

        $percent = [Math]::Min(99, [Math]::Max(0, [int](($StepIndex - 1) * 100 / $TotalSteps)))
        $activity = "Docker Engine setup in WSL ($DistroName)"
        Write-Progress -Activity $activity -Status "Step ${StepIndex}/${TotalSteps}: $StepName" -PercentComplete $percent

        $process = Start-Process -FilePath "wsl.exe" `
            -ArgumentList @("-d", $DistroName, "-e", "bash", $wslScriptPath) `
            -NoNewWindow `
            -PassThru `
            -RedirectStandardOutput $stdoutPath `
            -RedirectStandardError $stderrPath

        $startedAt = Get-Date
        while (-not $process.HasExited) {
            $elapsedSeconds = [int]((Get-Date) - $startedAt).TotalSeconds
            Write-Progress `
                -Activity $activity `
                -Status "Step ${StepIndex}/${TotalSteps}: $StepName (${elapsedSeconds}s elapsed)" `
                -PercentComplete $percent
            Start-Sleep -Seconds 1
            $process.Refresh()
        }

        $stdout = if (Test-Path $stdoutPath) { Get-Content -Raw $stdoutPath } else { "" }
        $stderr = if (Test-Path $stderrPath) { Get-Content -Raw $stderrPath } else { "" }
        if ($stdout) {
            Write-Host $stdout.TrimEnd()
        }
        if ($stderr) {
            Write-Host $stderr.TrimEnd() -ForegroundColor DarkYellow
        }

        if ($process.ExitCode -ne 0) {
            throw "WSL command failed with exit code $($process.ExitCode)"
        }
    } finally {
        Write-Progress -Activity "Docker Engine setup in WSL ($DistroName)" -Completed
        if (Test-Path $tempScript) {
            Remove-Item -LiteralPath $tempScript -Force
        }
        if (Test-Path $stdoutPath) {
            Remove-Item -LiteralPath $stdoutPath -Force
        }
        if (Test-Path $stderrPath) {
            Remove-Item -LiteralPath $stderrPath -Force
        }
    }
}

function Escape-ShellSingleQuoted {
    param([string]$Value)
    return "'" + ($Value -replace "'", "'\''") + "'"
}

if (-not (Test-CommandExists "wsl.exe")) {
    Write-ErrLog "wsl.exe was not found. Install WSL first from an administrator PowerShell: wsl --install"
}

Write-Info "Target WSL distro: $Distro"

if (-not (Test-WslDistro -Name $Distro)) {
    if ($SkipDistroInstall) {
        Write-ErrLog "WSL distro was not found: $Distro"
    }

    Write-WarnLog "The distro '$Distro' is not installed. Starting WSL installation."
    Write-WarnLog "If Windows asks for a reboot or Ubuntu first-user setup, finish it and rerun this script."
    & wsl.exe --install -d $Distro
    exit $LASTEXITCODE
}

if (-not $SkipDockerInstall) {
    Write-Info "Installing Docker Engine and Compose v2 inside $Distro."
    Write-Info "Ubuntu apt mirror: $UbuntuMirror"
    $escapedUbuntuMirror = Escape-ShellSingleQuoted -Value $UbuntuMirror
    $commonShell = @'
set -eu
if [ "$(id -u)" = "0" ]; then
  SUDO=""
else
  if ! command -v sudo >/dev/null 2>&1; then
    echo "sudo is required inside this WSL distro." >&2
    exit 1
  fi
  SUDO="sudo"
fi
APT_GET="$SUDO apt-get -o Acquire::Retries=5 -o Acquire::http::Timeout=30 -o Acquire::https::Timeout=30"
'@

    $steps = @(
        [PSCustomObject]@{
            Name = "Set Ubuntu apt mirror"
            Command = @"
mirror=$escapedUbuntuMirror
if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
  `$SUDO cp /etc/apt/sources.list.d/ubuntu.sources /etc/apt/sources.list.d/ubuntu.sources.team-info.bak
  `$SUDO sed -i "s|http://archive.ubuntu.com/ubuntu|`$mirror|g; s|https://archive.ubuntu.com/ubuntu|`$mirror|g" /etc/apt/sources.list.d/ubuntu.sources
fi
if [ -f /etc/apt/sources.list ]; then
  `$SUDO cp /etc/apt/sources.list /etc/apt/sources.list.team-info.bak
  `$SUDO sed -i "s|http://archive.ubuntu.com/ubuntu|`$mirror|g; s|https://archive.ubuntu.com/ubuntu|`$mirror|g" /etc/apt/sources.list
fi
"@
        },
        [PSCustomObject]@{
            Name = "Update apt package indexes"
            Command = @'
$APT_GET update
'@
        },
        [PSCustomObject]@{
            Name = "Install prerequisites"
            Command = @'
$APT_GET install -y ca-certificates curl
$SUDO install -m 0755 -d /etc/apt/keyrings
'@
        },
        [PSCustomObject]@{
            Name = "Add Docker apt repository"
            Command = @'
$SUDO curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
$SUDO chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
codename="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
arch="$(dpkg --print-architecture)"
$SUDO tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: ${codename}
Components: stable
Architectures: ${arch}
Signed-By: /etc/apt/keyrings/docker.asc
EOF
'@
        },
        [PSCustomObject]@{
            Name = "Refresh Docker package indexes"
            Command = @'
$APT_GET update
'@
        },
        [PSCustomObject]@{
            Name = "Install Docker Engine and Compose v2"
            Command = @'
$APT_GET install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
'@
        },
        [PSCustomObject]@{
            Name = "Start Docker Engine"
            Command = @'
if command -v systemctl >/dev/null 2>&1; then
  $SUDO systemctl enable --now docker || $SUDO systemctl start docker
else
  $SUDO service docker start
fi

if [ -n "${USER:-}" ] && [ "$USER" != "root" ] && ! id -nG "$USER" | grep -qw docker; then
  $SUDO usermod -aG docker "$USER"
fi
'@
        },
        [PSCustomObject]@{
            Name = "Verify Docker CLI"
            Command = @'
docker --version
docker compose version
'@
        }
    )

    for ($i = 0; $i -lt $steps.Count; $i++) {
        $step = $steps[$i]
        Invoke-WslShell `
            -DistroName $Distro `
            -Command ($commonShell + "`n" + $step.Command) `
            -StepName $step.Name `
            -StepIndex ($i + 1) `
            -TotalSteps $steps.Count
        Write-Ok "Step $($i + 1)/$($steps.Count) completed: $($step.Name)"
    }
}

[System.Environment]::SetEnvironmentVariable("TEAM_INFO_WSL_DISTRO", $Distro, "User")
$env:TEAM_INFO_WSL_DISTRO = $Distro

Write-Ok "TEAM_INFO_WSL_DISTRO saved: $Distro"
Write-WarnLog "If your user was added to the docker group, restart WSL before running docker without sudo:"
Write-Host "  wsl --shutdown"
Write-Host "  wsl -d $Distro -- docker ps"
Write-Ok "After that, run: & `"$env:TEAM_INFO_ROOT\run.ps1`" -Project current -Action ps"
