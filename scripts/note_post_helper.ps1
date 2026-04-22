# note_post_helper.ps1
# Usage: Right-click -> Run with PowerShell
# Or: powershell -ExecutionPolicy Bypass -File "scripts\note_post_helper.ps1"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir
$draftDir = Join-Path $baseDir "outputs\note\draft"
$postedDir = Join-Path $baseDir "outputs\note\posted"
$noteUrl = "https://note.com/notes/new"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  note Post Helper / Ayumi" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check draft folder
if (-not (Test-Path $draftDir)) {
    Write-Host "Draft folder not found:" -ForegroundColor Red
    Write-Host "   $draftDir"
    Read-Host "Press Enter to exit"
    exit
}

$mdFiles = Get-ChildItem -Path $draftDir -Filter "*.md" | Sort-Object Name
if ($mdFiles.Count -eq 0) {
    Write-Host "No articles in draft folder." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Show article list
Write-Host "Articles ready to post:" -ForegroundColor Green
for ($i = 0; $i -lt $mdFiles.Count; $i++) {
    Write-Host "  [$($i+1)] $($mdFiles[$i].Name)"
}
Write-Host ""

# Select article
$chosen = -1
while ($chosen -lt 0 -or $chosen -ge $mdFiles.Count) {
    $ans = Read-Host "Enter number (q to quit)"
    if ($ans -eq "q") { Write-Host "Exiting."; exit }
    $n = 0
    if ([int]::TryParse($ans, [ref]$n)) { $chosen = $n - 1 }
}

$selectedFile = $mdFiles[$chosen]
$filePath = $selectedFile.FullName

# Read and parse file
$rawContent = Get-Content -Path $filePath -Encoding UTF8 -Raw
$lineArray = $rawContent -split "`r?`n"

$title = ""
$bodyArr = New-Object System.Collections.Generic.List[string]
$titleFound = $false

foreach ($ln in $lineArray) {
    if (-not $titleFound -and $ln -match "^#\s+(.+)$") {
        $title = $matches[1].Trim()
        $titleFound = $true
    }
    else {
        $bodyArr.Add($ln)
    }
}

$bodyText = ($bodyArr -join "`n").Trim()
$charCount = $bodyText.Length

Write-Host ""
Write-Host "File      : $($selectedFile.Name)" -ForegroundColor Green
Write-Host "Title     : $title"
Write-Host "Length    : $charCount chars"

# Choose what to copy
Write-Host ""
Write-Host "Copy options:"
Write-Host "  [1] Body text only (recommended)"
Write-Host "  [2] Title + Body"
$copyAns = Read-Host "Choice (Enter=1)"
if ($copyAns -eq "2") {
    $clipText = "# $title`n`n$bodyText"
}
else {
    $clipText = $bodyText
}

# Copy to clipboard
try {
    Set-Clipboard -Value $clipText
    Write-Host ""
    Write-Host "Copied to clipboard!" -ForegroundColor Green
}
catch {
    Write-Host "Clipboard copy failed. Please copy manually:" -ForegroundColor Red
    Write-Host "   $filePath"
}

# Show title separately
Write-Host ""
Write-Host "Title (paste manually into note):" -ForegroundColor Yellow
Write-Host "   $title"

# Open note.com
Write-Host ""
$openAns = Read-Host "Open note.com in browser? (y/n)"
if ($openAns -eq "y") {
    Start-Process $noteUrl
    Write-Host "Opened note.com in browser." -ForegroundColor Green
}

# Posting instructions
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Posting steps:" -ForegroundColor Cyan
Write-Host "  1. Paste title into note title field"
Write-Host "     -> $title"
Write-Host "  2. Click body area, press Ctrl+V"
Write-Host "  3. Set thumbnail image from outputs\profile\"
Write-Host "  4. Publish"
Write-Host "================================================" -ForegroundColor Cyan

# Move to posted folder
Write-Host ""
$moveAns = Read-Host "Move file to posted folder after publishing? (y/n)"
if ($moveAns -eq "y") {
    if (-not (Test-Path $postedDir)) {
        New-Item -ItemType Directory -Path $postedDir | Out-Null
    }
    $dest = Join-Path $postedDir $selectedFile.Name
    Move-Item -Path $filePath -Destination $dest -Force
    Write-Host "Moved to:" -ForegroundColor Green
    Write-Host "   $dest"
}

Write-Host ""
Write-Host "Done! Good luck with your post." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
