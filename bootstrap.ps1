# 初回クローン後に一度だけ実行して setup コマンドを有効化するファイル。
# 使い方: . .\bootstrap.ps1
# エイリアス本体は setup 実行時に登録する。ターミナル起動時の自動チェックは行わない。

$_TeamInfoBootstrapRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function setup {
    & "$_TeamInfoBootstrapRoot\setup\setup_windows.ps1"
}

Write-Host "✅ setup コマンドが使えるようになりました" -ForegroundColor Green
Write-Host "   → PowerShell で setup と入力してセットアップを開始してください"
Write-Host "   （恒久的なコマンド登録は setup 実行中に行います）"
