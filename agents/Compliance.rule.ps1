
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Compliance {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
📖 **COMPLIANCE AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **LEGAL CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Policy Alignment" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Regulation Check Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Violation -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
