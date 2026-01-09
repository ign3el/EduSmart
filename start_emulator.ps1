# Start Android Emulator
$SDK_PATH = "C:\Users\sahte\AppData\Local\Android\Sdk"
$EMULATOR_TOOL = "$SDK_PATH\emulator\emulator.exe"
$ADB_TOOL = "$SDK_PATH\platform-tools\adb.exe"
$AVD_NAME = "Medium_Phone_API_36.1"

Write-Host "Starting Android Emulator: $AVD_NAME..." -ForegroundColor Green

# Kill existing if any
Get-Process -Name "emulator*" -ErrorAction SilentlyContinue | Stop-Process -Force

# Reset ADB
& $ADB_TOOL start-server

if (Test-Path $EMULATOR_TOOL) {
    # Use software rendering and cold boot to avoid graphics/snapshot issues
    & $EMULATOR_TOOL -avd $AVD_NAME -gpu swiftshader_indirect -no-snapshot-load
}
else {
    Write-Error "Emulator tool not found at $EMULATOR_TOOL"
}
