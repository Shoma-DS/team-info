# =============================================================================
# headroom installer (Windows) — トークン圧縮プロキシを claude / codex に配線
# =============================================================================
# 使い方（通常は setup_windows.ps1 から呼ばれる）:
#   powershell -ExecutionPolicy Bypass -File setup\headroom\install.ps1 `
#       -PythonExe "C:\path\to\python.exe" -RepoRoot "C:\path\to\team-info"
#
# 方針:
#   - artifacts\windows-x86_64\ に wheel があれば使う（Rust 不要・高速）
#   - 無ければその場でビルドし、artifacts にキャッシュ（要 Rust + MSVC build tools）
#   - Windows の Cargo 設定は既に ort-load-dynamic のため、実行時に onnxruntime.dll が必要
#   - 失敗しても warn のみ（呼び出し側 setup は止めない・非致命）
#
# ⚠️ このスクリプトは実機未検証です。初回実行時はログを確認してください。
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

# ── パスの決定 ───────────────────────────────────────────────────────────────
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $RepoRoot) { $RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path }
$Artifacts = Join-Path $RepoRoot "setup\headroom\artifacts"

# Python（pyenv-win 3.11 優先 → 引数 → python）
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    $pyenvPy = "$env:USERPROFILE\.pyenv\pyenv-win\versions\3.11.9\python.exe"
    if (Test-Path $pyenvPy) { $PythonExe = $pyenvPy }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $PythonExe = $cmd.Source }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    HrWarn "python が見つかりません。headroom をスキップします。"
    exit 1
}
HrInfo "Python: $PythonExe ($(& $PythonExe --version 2>&1))"

$UserBase  = (& $PythonExe -c "import site; print(site.USER_BASE)").Trim()
$ScriptsDir = Join-Path $UserBase "Scripts"
$HrBin = Join-Path $ScriptsDir "headroom.exe"
$HrHome = Join-Path $env:USERPROFILE ".headroom"
$OnnxDir = Join-Path $HrHome "lib"

# ── 機種判別（Windows）────────────────────────────────────────────────────────
$Arch = $env:PROCESSOR_ARCHITECTURE
$Platform = "windows-x86_64"
if ($Arch -eq "ARM64") { $Platform = "windows-arm64" }
HrStep "Headroom インストール (platform=$Platform)"

# ── Rust ツールチェーン ───────────────────────────────────────────────────────
function Ensure-Rust {
    if (Test-Cmd cargo) { return $true }
    $cargoBin = Join-Path $env:USERPROFILE ".cargo\bin"
    if (Test-Path (Join-Path $cargoBin "cargo.exe")) {
        $env:Path = "$cargoBin;$env:Path"
        if (Test-Cmd cargo) { return $true }
    }
    HrInfo "Rust ツールチェーンを導入します（rustup, 数分）..."
    try {
        if (Test-Cmd winget) {
            winget install --id Rustlang.Rustup --silent --accept-package-agreements --accept-source-agreements 2>&1 | Out-Null
        } else {
            $ru = Join-Path $env:TEMP "rustup-init.exe"
            Invoke-WebRequest -UseBasicParsing -Uri "https://win.rustup.rs/x86_64" -OutFile $ru
            & $ru -y --profile minimal 2>&1 | Out-Null
        }
    } catch { HrWarn "rustup 導入に失敗: $_" }
    $env:Path = "$cargoBin;$env:Path"
    return (Test-Cmd cargo)
}

# ── 2. wheel を入手 ──────────────────────────────────────────────────────────
HrStep "2. headroom wheel を入手"
$Wheel = $null
$cached = Get-ChildItem -Path (Join-Path $Artifacts $Platform) -Filter "headroom_ai-*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($cached) {
    $Wheel = $cached.FullName
    HrOk "同梱のビルド済み wheel を使用: $($cached.Name)"
} else {
    HrWarn "$Platform 用のビルド済み wheel がありません。ソースからビルドします（要 Rust + MSVC build tools）。"
    if (-not (Ensure-Rust)) {
        HrWarn "Rust を用意できませんでした。headroom 導入を中止します。"
        exit 1
    }
    HrInfo "cargo: $((Get-Command cargo -ErrorAction SilentlyContinue).Source)"
    $out = Join-Path $env:TEMP ("hr_wheel_build_" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    # Windows は Cargo 設定が既に load-dynamic のため通常ビルド（パッチ不要）
    HrInfo "wheel をビルド中（数分）..."
    try {
        & $PythonExe -m pip wheel --no-deps -w $out headroom-ai 2>&1 | Out-Null
    } catch {
        HrWarn "wheel ビルドに失敗: $_"
        exit 1
    }
    $built = Get-ChildItem -Path $out -Filter "headroom_ai-*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $built) { HrWarn "ビルド成果の wheel が見つかりません"; exit 1 }
    $Wheel = $built.FullName
    $dest = Join-Path $Artifacts $Platform
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item -Force $Wheel $dest
    HrOk "ビルド完了: $($built.Name) → artifacts\$Platform\ にキャッシュ"
}

# ── 3. 依存 + インストール & _core 確認 ──────────────────────────────────────
HrStep "3. 依存とインストール"
# proxy 実行に必要な純Python依存（fastapi/uvicorn/magika/zstandard/mcp/httpx[http2]/opentelemetry-api 等）
$HrVer = ([regex]::Match((Split-Path $Wheel -Leaf), '^headroom_ai-([0-9][^-]+)-')).Groups[1].Value
HrInfo "proxy 依存を導入中（数十MB・初回のみ）..."
try {
    & $PythonExe -m pip install --user "headroom-ai[proxy]==$HrVer" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { & $PythonExe -m pip install --user "headroom-ai[proxy]" 2>&1 | Out-Null }
} catch { HrWarn "proxy 依存の導入で警告（後続を続行）: $_" }
# _core 入り wheel を最終的に上書き
try {
    & $PythonExe -m pip install --user --force-reinstall --no-deps $Wheel 2>&1 | Out-Null
    HrOk "headroom-ai インストール完了（_core 入り wheel）"
} catch {
    HrWarn "pip install に失敗: $_"; exit 1
}
$coreOk = $false
try {
    Push-Location $env:USERPROFILE
    & $PythonExe -c "import headroom._core" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { $coreOk = $true }
} finally { Pop-Location }
if ($coreOk) { HrOk "Rust 拡張 headroom._core OK" }
else { HrWarn "headroom._core を import できません（wheel が _core 無しの可能性）"; exit 1 }

# ── 4. ONNX Runtime DLL を配置 ───────────────────────────────────────────────
HrStep "4. ONNX Runtime DLL を配置"
New-Item -ItemType Directory -Force -Path $OnnxDir | Out-Null
$OrtDll = Join-Path $OnnxDir "onnxruntime.dll"
$bundledDll = Get-ChildItem -Path (Join-Path $Artifacts $Platform) -Filter "onnxruntime*.dll" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($bundledDll) {
    Copy-Item -Force $bundledDll.FullName $OrtDll
    HrOk "同梱の onnxruntime.dll を配置: $OrtDll"
} elseif (Test-Path $OrtDll) {
    HrOk "既存の onnxruntime.dll を使用: $OrtDll"
} else {
    HrWarn "onnxruntime.dll が見つかりません。"
    HrWarn "  https://github.com/microsoft/onnxruntime/releases から win-x64 を入手し、"
    HrWarn "  $OrtDll に配置してください（圧縮時に必要）。"
}
# 環境変数（永続）
[System.Environment]::SetEnvironmentVariable("ORT_DYLIB_PATH", $OrtDll, "User")
$env:ORT_DYLIB_PATH = $OrtDll

# ── 5. claude / codex を配線 ─────────────────────────────────────────────────
HrStep "5. claude / codex を配線"
$env:HEADROOM_TELEMETRY = "off"
function Run-Hr { param($argline)
    try { & $HrBin @argline 2>&1 | Out-Null; return ($LASTEXITCODE -eq 0) } catch { return $false }
}
if (Run-Hr @("install","apply","--providers","manual","--target","claude","--no-telemetry")) {
    HrOk "常駐プロキシ＋claude ルーティングを設定"
} else { HrWarn "install apply で警告" }
if (Run-Hr @("init","-g","codex")) { HrOk "codex ルーティングを設定" } else { HrWarn "init codex で警告" }
if (Run-Hr @("mcp","install")) { HrOk "MCP retrieve を登録" } else { HrWarn "mcp install で警告" }

# 5-4. MCP 起動コマンドを絶対パス化 ＋ env に ORT/telemetry を注入
HrStep "5b. MCP 起動コマンドを絶対パス化"
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
    HrOk "MCP 起動コマンドを絶対パス化"
} catch { HrWarn "MCP 絶対パス化で警告: $_" } finally { Remove-Item -Force $tmpPy -ErrorAction SilentlyContinue }

# 5-5. PATH に headroom bin（Scripts）を追記
$cur = [System.Environment]::GetEnvironmentVariable("Path","User")
$parts = @(); if ($cur) { $parts = $cur.Split(";") | Where-Object { $_ } }
if ($parts -notcontains $ScriptsDir) {
    [System.Environment]::SetEnvironmentVariable("Path", (@($parts + $ScriptsDir) -join ";"), "User")
}
if ($env:Path -notlike "*$ScriptsDir*") { $env:Path = "$ScriptsDir;$env:Path" }
HrOk "PATH に headroom bin を追記"

# ── 6. 動作確認 ─────────────────────────────────────────────────────────────
HrStep "6. 動作確認"
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
        HrOk "プロキシ稼働中: ready=$($d.ready) rust_core=$($d.rust_core)"
    } catch { HrOk "プロキシ稼働中" }
    Write-Host ""
    HrOk "Headroom 導入完了。新しい PowerShell から claude / codex がプロキシ経由になります。"
    HrInfo "節約レポート: powershell -ExecutionPolicy Bypass -File `"$RepoRoot\setup\headroom\check.ps1`""
} else {
    HrWarn "プロキシの起動を確認できませんでした。~/.headroom\deploy\default\ のログを確認してください。"
    exit 1
}
