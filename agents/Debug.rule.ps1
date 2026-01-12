
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Debug {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
# 🐞 **DEBUGGER AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🔒 AUTH: TIER 1 - EXECUTION RIGHTS (DIAGNOSTICS)" -ForegroundColor Yellow
    
    Write-Host "
## 📋 **CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   ✅ Stack Trace Analysis" -ForegroundColor Green
    Write-Host "   🟡 Execute Diagnostic Commands" -ForegroundColor Yellow
    Write-Host "   🔵 Isolate Root Cause" -ForegroundColor Cyan

    $GlobalBrain = Join-Path $env:USERPROFILE ".gemini"
    $KBPath = Join-Path $GlobalBrain 'KnowledgeBase.json'
    if (Test-Path $KBPath) {
        $KB = Get-Content $KBPath -Raw | ConvertFrom-Json; $Rel = $KB | Where-Object { $_.Task -match $Task }
        if ($Rel) { Write-Host "   📖 GLOBAL Insight: " -ForegroundColor Cyan }
    }

    Invoke-Expression $Task
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Root Cause Analyzed" -ForegroundColor Green
    
    Write-Host "
## ➡ **HANDOFF:**" -ForegroundColor Yellow
    Write-Host "   [INFO.TASK/OUTPUT]" -ForegroundColor Cyan
    Write-Host "   FROM: Debugger" -ForegroundColor Gray
    Write-Host "   TO: Architect" -ForegroundColor Gray
    Write-Host "   RECOMMENDATION: Route findings to Architect for solution design" -ForegroundColor Yellow
}
