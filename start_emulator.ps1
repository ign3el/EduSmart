# Start Android Emulator
$SDK_PATH = "C:\Users\sahte\AppData\Local\Android\Sdk"
$EMULATOR_TOOL = "$SDK_PATH\emulator\emulator.exe"
$AVD_NAME = "Medium_Phone_API_36.1"

Write-Host "Starting Android Emulator: $AVD_NAME..." -ForegroundColor Green

if (Test-Path $EMULATOR_TOOL) {
    & $EMULATOR_TOOL -avd $AVD_NAME
} else {
    Write-Error "Emulator tool not found at $EMULATOR_TOOL"
}
