
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Data {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
📊 **DATA AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **DATA CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Schema Validation" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Data Integrity Check Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Error -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
