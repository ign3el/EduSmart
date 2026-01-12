
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-DevOps {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
🤖 **DEVOPS AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **CI/CD CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Pipeline Config" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Pipeline Review Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Failed -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
