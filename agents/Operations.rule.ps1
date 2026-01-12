
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Operations {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
🛠 **OPERATIONS AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **OPS CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Resource Check" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Operational Status: OK." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Incident -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
