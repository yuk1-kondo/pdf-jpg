$ErrorActionPreference = "Stop"

function Step($message) {
    Write-Host "`n==> $message" -ForegroundColor Cyan
}

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot

$iscc = Get-Command iscc -ErrorAction SilentlyContinue
$isccPath = $null

if ($iscc) {
    $isccPath = $iscc.Source
} else {
    $candidatePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidatePaths) {
        if (Test-Path $candidate) {
            $isccPath = $candidate
            break
        }
    }
}

if (-not $isccPath) {
    throw "ISCC.exe not found. Install Inno Setup first."
}

$installerScript = Join-Path $projectRoot "installer\NeonPDFShot.iss"
if (-not (Test-Path $installerScript)) {
    throw "Installer script not found: $installerScript"
}

Step "Compiling installer with Inno Setup"
& $isccPath $installerScript

Write-Host "`nInstaller build complete: dist-installer" -ForegroundColor Green
