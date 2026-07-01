# =============================================================================
# headroom installer (Windows)
# Wires the headroom token-compression proxy into claude / codex.
# =============================================================================
# Usage, usually called from setup_windows.ps1:
#   powershell -ExecutionPolicy Bypass -File setup\headroom\install.ps1 `
#       -PythonExe "C:\path\to\python.exe" -RepoRoot "C:\path\to\team-info"
#
# Policy:
#   - Use setup\headroom\artifacts\windows-x86_64\ wheel when available.
#   - Otherwise build from source and cache it under artifacts.
#   - Windows Cargo config uses ort-load-dynamic, so onnxruntime.dll is needed.
#   - Failures are warnings for the caller setup and are non-fatal there.
#
# This script may need environment-specific follow-up. Check logs on first run.
# =============================================================================

param(
    [string]$PythonExe = "",
    [string]$RepoRoot  = ""
)

$ErrorActionPreference = "Stop"

function HrInfo { param($m) Write-Host "[INFO]  $m" -ForegroundColor Cyan }
function HrOk   { param($m) Write-Host "[OK]    $m" -ForegroundColor Green }
function HrWarn { param($m) Write-Host "[WARN]  $m" -ForegroundColor Yellow }
function HrStep { param($m) Write-Host "`n=== $m ===" -ForegroundColor Magenta }
function Test-Cmd { param($c) return [bool](Get-Command $c -ErrorAction SilentlyContinue) }

# -- Path resolution -----------------------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path }
$Artifacts = Join-Path $RepoRoot "setup\headroom\artifacts"

# Python: prefer pyenv-win 3.11, then argument, then python on PATH.
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    $pyenvPy = "$env:USERPROFILE\.pyenv\pyenv-win\versions\3.11.9\python.exe"
    if (Test-Path $pyenvPy) { $PythonExe = $pyenvPy }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $PythonExe = $cmd.Source }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    HrWarn "python not found. Skipping headroom."
    exit 1
}
HrInfo "Python: $PythonExe ($(& $PythonExe --version 2>&1))"

$UserBase  = (& $PythonExe -c "import site; print(site.USER_BASE)").Trim()
$ScriptsDir = Join-Path $UserBase "Scripts"
$HrBin = Join-Path $ScriptsDir "headroom.exe"
$HrHome = Join-Path $env:USERPROFILE ".headroom"
$OnnxDir = Join-Path $HrHome "lib"

# -- Platform detection --------------------------------------------------------
$Arch = $env:PROCESSOR_ARCHITECTURE
$Platform = "windows-x86_64"
if ($Arch -eq "ARM64") { $Platform = "windows-arm64" }
HrStep "Headroom install (platform=$Platform)"

# -- Rust toolchain ------------------------------------------------------------
function Ensure-Rust {
    if (Test-Cmd cargo) { return $true }
    $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
    if (Test-Path (Join-Path $cargoBin "cargo.exe")) {
        $env:Path = "$cargoBin;$env:Path"
        if (Test-Cmd cargo) { return $true }
    }
    HrInfo "Installing Rust toolchain (rustup, may take several minutes)..."
    try {
        if (Test-Cmd winget) {
            winget install --id Rustlang.Rustup --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        } else {
            $ru = Join-Path $env:TEMP "rustup-init.exe"
            Invoke-WebRequest -UseBasicParsing -Uri "https://win.rustup.rs/x86_64" -OutFile $ru
            & $ru -y --profile minimal 2>&1 | Out-Null
        }
    } catch { HrWarn "rustup install failed: $_" }
    $env:Path = "$cargoBin;$env:Path"
    return (Test-Cmd cargo)
}

# -- 2. Get wheel --------------------------------------------------------------
HrStep "2. Get headroom wheel"
$Wheel = $null
$cached = Get-ChildItem -Path (Join-Path $Artifacts $Platform) -Filter "headroom_ai-*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($cached) {
    $Wheel = $cached.FullName
    HrOk "Using bundled prebuilt wheel: $($cached.Name)"
} else {
    HrWarn "No prebuilt wheel for $Platform. Building from source (requires Rust + MSVC build tools)."
    if (-not (Ensure-Rust)) {
        HrWarn "Rust is unavailable. Aborting headroom install."
        exit 1
    }
    HrInfo "cargo: $((Get-Command cargo -ErrorAction SilentlyContinue).Source)"
    $out = Join-Path $env:TEMP ("hr_wheel_build_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    # Windows Cargo config already uses load-dynamic, so no patch is needed.
    HrInfo "Building wheel (may take several minutes)..."
    try {
        & $PythonExe -m pip wheel --no-deps -w $out headroom-ai 2>&1 | Out-Null
    } catch {
        HrWarn "wheel build failed: $_"
        exit 1
    }
    $built = Get-ChildItem -Path $out -Filter "headroom_ai-*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $built) { HrWarn "Built wheel not found"; exit 1 }
    $Wheel = $built.FullName
    $dest = Join-Path $Artifacts $Platform
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item -Force $Wheel $dest
    HrOk "Build complete: $($built.Name), cached under artifacts\$Platform\"
}

# -- 3. Dependencies, install, and _core check ---------------------------------
HrStep "3. Install dependencies"
# Pure-Python proxy dependencies.
$HrVer = ([regex]::Match((Split-Path $Wheel -Leaf), '^headroom_ai-([0-9][^-]+)-')).Groups[1].Value
HrInfo "Installing proxy dependencies (tens of MB on first run)..."
try {
    & $PythonExe -m pip install --user "headroom-ai[proxy]==$HrVer" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { & $PythonExe -m pip install --user "headroom-ai[proxy]" 2>&1 | Out-Null }
} catch { HrWarn "proxy dependency install warning, continuing: $_" }
# Finally overwrite with the wheel that contains _core.
try {
    & $PythonExe -m pip install --user --force-reinstall --no-deps $Wheel 2>&1 | Out-Null
    HrOk "headroom-ai install complete (wheel with _core)"
} catch {
    HrWarn "pip install failed: $_"; exit 1
}
$coreOk = $false
try {
    Push-Location $env:USERPROFILE
    & $PythonExe -c "import headroom._core" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $coreOk = $true }
} finally { Pop-Location }
if ($coreOk) { HrOk "Rust extension headroom._core OK" }
else { HrWarn "Cannot import headroom._core. The wheel may not include _core."; exit 1 }

# -- 4. Place ONNX Runtime DLL -------------------------------------------------
HrStep "4. Place ONNX Runtime DLL"
New-Item -ItemType Directory -Force -Path $OnnxDir | Out-Null
$OrtDll = Join-Path $OnnxDir "onnxruntime.dll"
$bundledDll = Get-ChildItem -Path (Join-Path $Artifacts $Platform) -Filter "onnxruntime*.dll" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($bundledDll) {
    Copy-Item -Force $bundledDll.FullName $OrtDll
    HrOk "Bundled onnxruntime.dll copied to: $OrtDll"
} elseif (Test-Path $OrtDll) {
    HrOk "Using existing onnxruntime.dll: $OrtDll"
} else {
    HrWarn "onnxruntime.dll not found."
    HrWarn "  Download win-x64 from https://github.com/microsoft/onnxruntime/releases"
    HrWarn "  and place it at $OrtDll. It is required for compression."
}
# User environment variables.
[System.Environment]::SetEnvironmentVariable("ORT_DYLIB_PATH", $OrtDll, "User")
$env:ORT_DYLIB_PATH = $OrtDll

# -- 5. Wire claude / codex ----------------------------------------------------
HrStep "5. Wire claude / codex"
$env:HEADROOM_TELEMETRY = "off"
function Run-Hr { param($argline)
    try { & $HrBin @argline 2>&1 | Out-Null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}
if (Run-Hr @("install","apply","--providers","manual","--target","claude","--no-telemetry")) {
    HrOk "Resident proxy and claude routing configured"
} else { HrWarn "install apply warning" }
if (Run-Hr @("init","-g","codex")) { HrOk "codex routing configured" } else { HrWarn "init codex warning" }
if (Run-Hr @("mcp","install")) { HrOk "MCP retrieve registered" } else { HrWarn "mcp install warning" }

# 5-4. Convert MCP command to absolute path and inject ORT/telemetry env.
HrStep "5b. Convert MCP command to absolute path"
$absPy = @'
import json, os, sys
hrbin = sys.argv[1]; dy = sys.argv[2]
cp = os.path.expanduser('~/.claude.json')
if os.path.exists(cp):
    try:
        d = json.load(open(cp, encoding='utf-8')); n = 0
        def walk(o):
            global n
            if isinstance(o, dict):
                m = o.get('mcpServers')
                if isinstance(m, dict) and 'headroom' in m:
                    h = m['headroom']; h['command'] = hrbin
                    h.setdefault('env', {})
                    if dy: h['env']['ORT_DYLIB_PATH'] = dy
                    h['env']['HEADROOM_TELEMETRY'] = 'off'; n += 1
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for x in o: walk(x)
        walk(d)
        if n: json.dump(d, open(cp, 'w', encoding='utf-8'), indent=2)
    except Exception as e:
        print('claude.json patch skipped:', e)
tp = os.path.expanduser('~/.codex/config.toml')
if os.path.exists(tp):
    s = open(tp, encoding='utf-8').read()
    s2 = s.replace('command = "headroom"', 'command = "%s"' % hrbin.replace('\\', '\\\\'))
    if s2 != s: open(tp, 'w', encoding='utf-8').write(s2)
'@
$tmpPy = Join-Path $env:TEMP ("hr_abs_" + [guid]::NewGuid().ToString("N") + ".py")
Set-Content -Path $tmpPy -Value $absPy -Encoding UTF8
try {
    & $PythonExe $tmpPy $HrBin $OrtDll 2>&1 | Out-Null
    HrOk "MCP command converted to absolute path"
} catch { HrWarn "MCP absolute-path patch warning: $_" } finally { Remove-Item -Force $tmpPy -ErrorAction SilentlyContinue }

# 5-5. Add headroom bin (Scripts) to PATH.
$cur = [System.Environment]::GetEnvironmentVariable("Path","User")
$parts = @(); if ($cur) { $parts = $cur.Split(";") | Where-Object { $_ } }
if ($parts -notcontains $ScriptsDir) {
    [System.Environment]::SetEnvironmentVariable("Path", (@($parts + $ScriptsDir) -join ";"), "User")
}
if ($env:Path -notlike "*$ScriptsDir*") { $env:Path = "$ScriptsDir;$env:Path" }
HrOk "Added headroom bin to PATH"

# -- 6. Smoke test -------------------------------------------------------------
HrStep "6. Smoke test"
$Port = if ($env:HEADROOM_PORT) { $env:HEADROOM_PORT } else { "8787" }
$ready = $false
for ($i = 0; $i -lt 25; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://127.0.0.1:$Port/readyz"
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch { Start-Sleep -Seconds 2 }
}
if ($ready) {
    try {
        $d = (Invoke-WebRequest -UseBasicParsing -TimeoutSec 5 -Uri "http://127.0.0.1:$Port/readyz").Content | ConvertFrom-Json
        HrOk "Proxy is running: ready=$($d.ready) rust_core=$($d.rust_core)"
    } catch { HrOk "Proxy is running" }
    Write-Host ""
    HrOk "Headroom install complete. New PowerShell sessions will route claude / codex through the proxy."
    HrInfo "Savings report: powershell -ExecutionPolicy Bypass -File `"$RepoRoot\setup\headroom\check.ps1`""
} else {
    HrWarn "Proxy readiness was not confirmed. Check logs under ~/.headroom/deploy/default/."
    exit 1
}
