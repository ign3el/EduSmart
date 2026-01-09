# Build Android App
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$GRADLE_WRAPPER = ".\android_app\gradlew.bat"

if (-not (Test-Path $GRADLE_WRAPPER)) {
    Write-Error "Gradle wrapper not found at $GRADLE_WRAPPER. Make sure you are in the project root."
    exit 1
}

Write-Host "Using JAVA_HOME: $env:JAVA_HOME" -ForegroundColor Cyan
Write-Host "Starting Build..." -ForegroundColor Green

& $GRADLE_WRAPPER build
