# Force Kill Emulator and ADB
Write-Host "Killing Emulator and ADB processes..." -ForegroundColor Yellow

Get-Process -Name "emulator*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "adb" -ErrorAction SilentlyContinue | Stop-Process -Force

Start-Sleep -Seconds 2

Write-Host "Removing stale lock files..." -ForegroundColor Yellow
$AVD_PATH = "C:\Users\sahte\.android\avd\Medium_Phone.avd"
if (Test-Path $AVD_PATH) {
    Remove-Item "$AVD_PATH\*.lock" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "Locks removed from $AVD_PATH" -ForegroundColor Gray
}
else {
    Write-Warning "AVD Directory not found at $AVD_PATH"
}

Write-Host "Resetting ADB..." -ForegroundColor Green
$SDK_PATH = "C:\Users\sahte\AppData\Local\Android\Sdk"
& "$SDK_PATH\platform-tools\adb.exe" kill-server
& "$SDK_PATH\platform-tools\adb.exe" start-server

Write-Host "Cleanup Complete." -ForegroundColor Green
