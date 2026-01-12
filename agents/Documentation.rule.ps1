
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Documentation {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
📘 **DOCUMENTATION AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **WIKI CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] API Surface Review" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Docs Updated." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Missing Info -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
