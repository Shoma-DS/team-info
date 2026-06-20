# headroom 節約レポート（小学生むけ表示・Windows 版）
# 使い方: powershell -ExecutionPolicy Bypass -File setup\headroom\check.ps1
# 「前回このボタンを押してから、今回どれだけ言葉をへらせたか」を出します。

$ErrorActionPreference = "Stop"
$Port = if ($env:HEADROOM_PORT) { $env:HEADROOM_PORT } else { "8787" }
$Snap = Join-Path $HOME ".headroom\.last_snapshot.json"

try {
    $resp = Invoke-WebRequest -UseBasicParsing -TimeoutSec 8 -Uri "http://127.0.0.1:$Port/stats"
    $d = $resp.Content | ConvertFrom-Json
} catch {
    Write-Host "⚠️ 通訳さん（headroom）が今うごいていないみたいです。"
    Write-Host "   少し待ってからもう一度ためしてください。"
    exit 0
}

$agents = @()
if ($d.agent_usage -and $d.agent_usage.agents) { $agents = $d.agent_usage.agents }

$before = 0; $after = 0; $saved = 0; $reqs = 0
foreach ($a in $agents) {
    $b = [int]($a.before_tokens)
    $before += $b
    $after  += if ($null -ne $a.after_tokens) { [int]$a.after_tokens } else { $b }
    $saved  += [int]($a.tokens_saved)
    $reqs   += [int]($a.requests)
}
$cacheUsd = 0.0
try { $cacheUsd = [double]$d.summary.cost.breakdown.cache_savings_usd } catch { $cacheUsd = 0.0 }

$prev = $null
if (Test-Path $Snap) {
    try { $prev = Get-Content $Snap -Raw | ConvertFrom-Json } catch { $prev = $null }
}

function Show-Block($title, $b, $a, $sv, $rq, $cu) {
    $pct = if ($b) { ($sv / $b) * 100 } else { 0 }
    Write-Host "=== $title ==="
    Write-Host ("  AIとのやりとり: {0} 回" -f $rq)
    Write-Host ("  送った言葉    : {0:N0} → {1:N0} （{2:N0} 言葉をへらせた／{3:F1}%）" -f $b, $a, $sv, $pct)
    if ($cu -and $cu -gt 0) {
        Write-Host ("  キャッシュでの節約: 約 `${0:F2} 相当" -f $cu)
    }
    if ($sv -eq 0 -and $cu -le 0) {
        Write-Host "  → 今回は へらせた言葉が ほぼ 0 でした。"
        Write-Host "     （短いやりとりだと へりにくいです。長い作業ほど効きます）"
    }
    Write-Host ""
}

if ($prev) {
    $db = $before - [int]($prev.before)
    $da = $after  - [int]($prev.after)
    $ds = $saved  - [int]($prev.saved)
    $dr = $reqs   - [int]($prev.reqs)
    $dc = $cacheUsd - [double]($prev.cache_usd)
    if ($dr -gt 0) {
        Show-Block "前回チェックからの今回ぶん" $db $da $ds $dr $dc
    } else {
        Write-Host "=== 前回チェックからの今回ぶん ==="
        Write-Host "  前回からまだ新しいやりとりがありません。"
        Write-Host "  claude や codex を使ってから、もう一度押してください。"
        Write-Host ""
    }
}

Show-Block "通訳さんを雇ってからの合計" $before $after $saved $reqs $cacheUsd

$snapDir = Split-Path $Snap -Parent
if (-not (Test-Path $snapDir)) { New-Item -ItemType Directory -Force -Path $snapDir | Out-Null }
[ordered]@{ before=$before; after=$after; saved=$saved; reqs=$reqs; cache_usd=$cacheUsd } |
    ConvertTo-Json | Set-Content -Path $Snap -Encoding UTF8

Write-Host "（このボタンを押した時点を記録しました。次に押すと『そこから今回ぶん』が出ます）"
