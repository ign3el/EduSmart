# Start Android Emulator
$SDK_PATH = "C:\Users\sahte\AppData\Local\Android\Sdk"
$EMULATOR_TOOL = "$SDK_PATH\emulator\emulator.exe"
$ADB_TOOL = "$SDK_PATH\platform-tools\adb.exe"

# Dynamically get the first AVD
$AVD_NAME = & $EMULATOR_TOOL -list-avds | Select-Object -First 1
Write-Host "Detected AVD: $AVD_NAME" -ForegroundColor Cyan

Write-Host "Starting Android Emulator: $AVD_NAME..." -ForegroundColor Green


# Kill existing if any
Get-Process -Name "emulator*" -ErrorAction SilentlyContinue | Stop-Process -Force

# Run Deep Clean
Write-Host "Running Deep Clean..." -ForegroundColor Yellow
.\fix_emulator.ps1

# Reset ADB
& $ADB_TOOL start-server

if (Test-Path $EMULATOR_TOOL) {
    # Use software rendering, cold boot, and read-only to bypass locks
    & $EMULATOR_TOOL -avd $AVD_NAME -gpu swiftshader_indirect -no-snapshot-load -read-only
}
else {
    Write-Error "Emulator tool not found at $EMULATOR_TOOL"
}
