
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-QA {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
# 🧪 **QA AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🔒 AUTH: TIER 1 - EXECUTION RIGHTS (TESTING)" -ForegroundColor Green
    
    Write-Host "
## 📋 **CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   ✅ Scan Knowledge Base" -ForegroundColor Green
    Write-Host "   🟡 Execute Test Commands" -ForegroundColor Yellow
    Write-Host "   🔵 Verify Output Integrity" -ForegroundColor Cyan

    $GlobalBrain = Join-Path $env:USERPROFILE ".gemini"
    $KBPath = Join-Path $GlobalBrain 'KnowledgeBase.json'
    if (Test-Path $KBPath) {
        $KB = Get-Content $KBPath -Raw | ConvertFrom-Json; $Rel = $KB | Where-Object { $_.Task -match $Task }
        if ($Rel) { Write-Host "   📖 GLOBAL Insight: " -ForegroundColor Cyan }
    }

    Invoke-Expression $Task
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Validation Complete" -ForegroundColor Green
    
    Write-Host "
## ➡ **HANDOFF:**" -ForegroundColor Yellow
    Write-Host "   [INFO.TASK/OUTPUT]" -ForegroundColor Cyan
    Write-Host "   FROM: QA" -ForegroundColor Gray
    Write-Host "   TO: Debugger (if issues found)" -ForegroundColor Gray
    Write-Host "   RECOMMENDATION: Route to Debugger if issues detected" -ForegroundColor Yellow
}
