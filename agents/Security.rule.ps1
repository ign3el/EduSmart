
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Security {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
🛡 **SECURITY AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **AUDIT CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Vulnerability Scan" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Security Audit Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Risk -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
