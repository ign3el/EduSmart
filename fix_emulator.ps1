# Force Kill Emulator and ADB
Write-Host "Killing Emulator and ADB processes..." -ForegroundColor Yellow

Get-Process -Name "emulator*" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "adb" -ErrorAction SilentlyContinue | Stop-Process -Force

Start-Sleep -Seconds 2

Write-Host "Removing stale lock files..." -ForegroundColor Yellow
# Try to find the .avd folder in standard location or current directory
$HOME_ANDROID = "$env:USERPROFILE\.android\avd"
$AVD_FOLDERS = Get-ChildItem -Path $HOME_ANDROID -Filter "*.avd"

foreach ($folder in $AVD_FOLDERS) {
    $path = $folder.FullName
    Write-Host "Cleaning locks in: $path" -ForegroundColor Gray
    Remove-Item "$path\*.lock" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "$path\*.qcow2" -Force -ErrorAction SilentlyContinue # Clean qcow2 diffs if corrupted
}

# Clean global locks in .android
$GLOBAL_LOCKS = "$env:USERPROFILE\.android\*.lock"
Remove-Item $GLOBAL_LOCKS -Force -ErrorAction SilentlyContinue

Write-Host "Resetting ADB..." -ForegroundColor Green
$SDK_PATH = "C:\Users\sahte\AppData\Local\Android\Sdk"
& "$SDK_PATH\platform-tools\adb.exe" kill-server
& "$SDK_PATH\platform-tools\adb.exe" start-server

Write-Host "Cleanup Complete." -ForegroundColor Green
