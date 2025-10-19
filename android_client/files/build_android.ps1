Write-Host "Starting Android app build..." -ForegroundColor Green

# Check if buildozer is installed
if (Get-Command buildozer -ErrorAction SilentlyContinue) {
    Write-Host "Buildozer is already installed" -ForegroundColor Yellow
} else {
    Write-Host "Installing buildozer..." -ForegroundColor Yellow
    pip install buildozer
}

# Execute buildozer command to build APK
Write-Host "Building APK with buildozer..." -ForegroundColor Green
buildozer android debug

Write-Host "Build completed!" -ForegroundColor Green
Write-Host "APK file is located in bin directory" -ForegroundColor Yellow
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")