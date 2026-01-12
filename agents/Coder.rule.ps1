[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Coder {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "`n# 💻 **CODER AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🔒 AUTH: TIER 2 - FILE WRITE ONLY" -ForegroundColor Magenta

    Write-Host "`n## 📋 **CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   ✅ Parse Blueprint" -ForegroundColor Green
    Write-Host "   🟡 Apply Code Changes" -ForegroundColor Yellow
    Write-Host "   🔵 Verify Syntax" -ForegroundColor Cyan

    Write-Host "`n   📝 Generating Visual Diff..." -ForegroundColor Gray
    Write-Host "   <<<< OLD CODE BLOCK" -ForegroundColor Red
    Write-Host "   ==== (Editing)" -ForegroundColor Gray
    Write-Host "   >>>> NEW CODE BLOCK" -ForegroundColor Green
    
    Write-Host "   💾 Saving to filesystem..." -ForegroundColor Magenta
    Start-Sleep -Milliseconds 250
    Write-Host "   ✅ Implementation Complete." -ForegroundColor Green
    
    Write-Host "`n## ➡ **HANDOFF:**" -ForegroundColor Yellow
    Write-Host "   [INFO.TASK/OUTPUT]" -ForegroundColor Cyan
    Write-Host "   FROM: Coder" -ForegroundColor Gray
    Write-Host "   TO: SME" -ForegroundColor Gray
    Write-Host "   RECOMMENDATION: Route to SME for Verification" -ForegroundColor Yellow
}
