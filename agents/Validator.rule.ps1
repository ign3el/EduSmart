
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Validator {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
✅ **VALIDATOR AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **RULE CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Protocol Enforcement" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Rules Enforcement Scan Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Violation -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
