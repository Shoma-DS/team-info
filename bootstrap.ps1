# 初回クローン後に一度だけ実行して setup コマンドを有効化するファイル。
# 使い方: . .\bootstrap.ps1
# このスクリプトは PowerShell プロファイルに自動チェック行も追記する。

$_TeamInfoBootstrapRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$_Script = "$_TeamInfoBootstrapRoot\.agent\skills\common\scripts\register_aliases.py"

function setup {
    & "$_TeamInfoBootstrapRoot\setup\setup_windows_safe.ps1"
}

# PowerShell プロファイルに自動チェック行を追記
$profileDir = Split-Path -Parent $PROFILE
if (-not (Test-Path $profileDir)) { New-Item -ItemType Directory -Path $profileDir -Force | Out-Null }
if (-not (Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force | Out-Null }
$profileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
if ($profileContent -notlike "*team-info alias auto-check*") {
    $hookLine = @"

# team-info alias auto-check
if (-not (Test-Path "`$HOME\.config\team-info\aliases-registered")) {
    if (Test-Path "$_Script") { python "$_Script" --root "$_TeamInfoBootstrapRoot" 2>`$null }
}
"@
    Add-Content -Path $PROFILE -Value $hookLine
}

Write-Host "✅ setup コマンドが使えるようになりました" -ForegroundColor Green
Write-Host "   → PowerShell で setup と入力してセットアップを開始してください"
Write-Host "   （次回ターミナル起動時から自動登録が走ります）"
