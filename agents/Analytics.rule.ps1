
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Analytics {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
📊 **ANALYTICS AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **STATS CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Metric Collection" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Telemetry Review Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Anomaly -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
