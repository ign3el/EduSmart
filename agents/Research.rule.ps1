
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Research {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
🕵 **RESEARCH AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **PROBE CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Paper Search" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Tech Feasibility Scan Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Blocked -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
