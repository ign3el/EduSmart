[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Orchestrator {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "`n# 🎛 **ORCHESTRATOR AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🔒 AUTH: TIER 1 - EXECUTION RIGHTS" -ForegroundColor Red
    
    Write-Host "`n## 📋 **CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   ✅ Initialize Identity" -ForegroundColor Green
    Write-Host "   🟡 Consult Global Knowledge Base" -ForegroundColor Yellow
    Write-Host "   🔵 Execute Command Stream" -ForegroundColor Cyan

    # GLOBAL KB LOOKUP
    $GlobalBrain = Join-Path $env:USERPROFILE ".gemini"
    $KBPath = Join-Path $GlobalBrain 'KnowledgeBase.json'
    
    if (Test-Path $KBPath) {
        $KB = Get-Content $KBPath -Raw | ConvertFrom-Json
        $Relevant = $KB | Where-Object { $_.Task -match $Task }
        if ($Relevant) { Write-Host "   📖 GLOBAL Insight: $($Relevant.Note | Select-Object -First 1)" -ForegroundColor Cyan }
    }
    
    Invoke-Expression $Task | Tee-Object -FilePath (Join-Path $ProjectFolder 'ANTIGRAVITY_TRANSCRIPT.log') -Append
    Write-Host "   ✅ Mission Status: COMPLETE" -ForegroundColor Green
}
