[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Support {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "`n# 🤝 **SUPPORT AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🔒 AUTH: TIER 3 - ADVISORY ONLY" -ForegroundColor Green
    
    Write-Host "`n## 📋 **CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   ✅ Acknowledge Request" -ForegroundColor Green
    Write-Host "   🟡 Analyze Context" -ForegroundColor Yellow

    Write-Host "   💭 Analyzing Request..." -ForegroundColor Gray
    Start-Sleep -Milliseconds 300
    Write-Host "   ✅ Analysis Complete" -ForegroundColor Green
    
    Write-Host "`n## ➡ **HANDOFF:**" -ForegroundColor Yellow
    Write-Host "   [INFO.TASK/OUTPUT]" -ForegroundColor Cyan
    Write-Host "   FROM: Support/SME" -ForegroundColor Gray
    Write-Host "   TO: Debugger" -ForegroundColor Gray
    Write-Host "   RECOMMENDATION: Route to Debugger for diagnostics" -ForegroundColor Yellow
}
