param(
    [string]$AppName = "NeonPDFShot",
    [string]$PythonExe = "python",
    [switch]$OneFile
)

$ErrorActionPreference = "Stop"

function Step($message) {
    Write-Host "`n==> $message" -ForegroundColor Cyan
}

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot

$venvPath = Join-Path $projectRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

Step "Creating virtual environment"
if (-not (Test-Path $venvPath)) {
    & $PythonExe -m venv $venvPath
}

Step "Installing dependencies"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt pyinstaller

Step "Cleaning old build artifacts"
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }
if (Test-Path "$AppName.spec") { Remove-Item "$AppName.spec" -Force }

$pyinstallerArgs = @(
    "--noconfirm",
    "--windowed",
    "--name", $AppName,
    "app.py"
)

if ($OneFile) {
    $pyinstallerArgs = @("--onefile") + $pyinstallerArgs
}

Step "Building executable with PyInstaller"
& $venvPython -m PyInstaller @pyinstallerArgs

if ($OneFile) {
    Write-Host "`nBuild complete: dist\$AppName.exe" -ForegroundColor Green
} else {
    Write-Host "`nBuild complete: dist\$AppName\$AppName.exe" -ForegroundColor Green
}
