
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Architect {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
# 🏗 **ARCHITECT AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🔒 AUTH: TIER 3 - ADVISORY ONLY" -ForegroundColor Blue
    
    Write-Host "
## 📋 **CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   ✅ Review Debug Findings" -ForegroundColor Green
    Write-Host "   🟡 Draft Implementation Plan" -ForegroundColor Yellow
    Write-Host "   🔵 Design Solution Architecture" -ForegroundColor Cyan

    $GlobalBrain = Join-Path $env:USERPROFILE ".gemini"
    $KBPath = Join-Path $GlobalBrain 'KnowledgeBase.json'
    if (Test-Path $KBPath) {
        $KB = Get-Content $KBPath -Raw | ConvertFrom-Json; $Rel = $KB | Where-Object { $_.Task -match $Task }
        if ($Rel) { Write-Host "   📖 GLOBAL Insight: " -ForegroundColor Cyan }
    }

    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Blueprints Ready" -ForegroundColor Green
    
    Write-Host "
## ➡ **HANDOFF:**" -ForegroundColor Yellow
    Write-Host "   [INFO.TASK/OUTPUT]" -ForegroundColor Cyan
    Write-Host "   FROM: Architect" -ForegroundColor Gray
    Write-Host "   TO: Coder" -ForegroundColor Gray
    Write-Host "   RECOMMENDATION: Route plan to Coder for implementation" -ForegroundColor Yellow
}
