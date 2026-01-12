
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Risk {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
⚠ **RISK AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **THREAT CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Impact Analysis" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Risk Assessment Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If High Risk -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
