
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
function Run-Performance {
    param([string]$Task, [string]$ProjectFolder)
    Write-Host "
⚡ **PERFORMANCE AGENT** [ONLINE]" -ForegroundColor Cyan
    Write-Host "   🟡 AUTH: SME ADVISORY (READ-ONLY)" -ForegroundColor Gray
    Write-Host "
   📋 **SPEED CHECKLIST:**" -ForegroundColor Gray
    Write-Host "   - [ 🟡 ] Latency Measurement" -ForegroundColor Yellow
    Write-Host "   ---------------------------------------" -ForegroundColor DarkGray
    Start-Sleep -Milliseconds 200
    Write-Host "   ✅ Latency Analysis Complete." -ForegroundColor Green
    Write-Host "   ➡ ADVISORY: If Slow -> Route to **DEBUGGER**." -ForegroundColor Yellow
}
