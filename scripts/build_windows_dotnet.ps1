param(
    [string]$Runtime = "win-x64",
    [string]$Configuration = "Release",
    [switch]$SingleFile
)

$ErrorActionPreference = "Stop"

function Step($message) {
    Write-Host "`n==> $message" -ForegroundColor Cyan
}

$projectRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $projectRoot

$projectFile = "dotnet\NeonPdfShot.DotNet\NeonPdfShot.DotNet.csproj"
$outputDir = "dist-dotnet\NeonPDFShot"

Step "Cleaning old .NET build artifacts"
if (Test-Path "dist-dotnet") { Remove-Item "dist-dotnet" -Recurse -Force }

$publishArgs = @(
    "publish",
    $projectFile,
    "-c", $Configuration,
    "-r", $Runtime,
    "--self-contained", "true",
    "-p:PublishTrimmed=false",
    "-o", $outputDir
)

if ($SingleFile) {
    $publishArgs += "-p:PublishSingleFile=true"
    $publishArgs += "-p:IncludeNativeLibrariesForSelfExtract=true"
}

Step "Publishing .NET desktop app"
dotnet @publishArgs

Write-Host "`nBuild complete: $outputDir" -ForegroundColor Green
