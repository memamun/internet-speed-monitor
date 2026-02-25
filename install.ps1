# SpeedMonitor Installer
# Usage: irm https://raw.githubusercontent.com/memamun/internet-speed-monitor/master/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$repo    = "memamun/internet-speed-monitor"
$appName = "SpeedMonitor"

Write-Host "`n$appName Installer" -ForegroundColor Cyan
Write-Host "===========================`n" -ForegroundColor Cyan

# Get the latest release from GitHub
Write-Host "Fetching latest release..." -ForegroundColor Yellow
$release = Invoke-RestMethod "https://api.github.com/repos/$repo/releases/latest"
$version = $release.tag_name
Write-Host "Found version: $version" -ForegroundColor Green

# Find the setup installer asset
$asset = $release.assets | Where-Object { $_.name -like "*Setup*.exe" } | Select-Object -First 1

if (-not $asset) {
    # Fall back to bare .exe if no setup found
    $asset = $release.assets | Where-Object { $_.name -eq "SpeedMonitor.exe" } | Select-Object -First 1
}

if (-not $asset) {
    Write-Error "No installer found in the latest release. Please visit: https://github.com/$repo/releases/latest"
    exit 1
}

$downloadUrl = $asset.browser_download_url
$fileName    = $asset.name
$tempPath    = Join-Path $env:TEMP $fileName

# Download
Write-Host "Downloading $fileName..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath -UseBasicParsing

Write-Host "Download complete!" -ForegroundColor Green

# Run the installer silently (Inno Setup supports /SILENT or /VERYSILENT)
if ($fileName -like "*Setup*") {
    Write-Host "Running installer silently..." -ForegroundColor Yellow
    Start-Process -FilePath $tempPath -ArgumentList "/SILENT", "/SUPPRESSMSGBOXES", "/NORESTART" -Wait
    Write-Host "`n$appName $version installed successfully!" -ForegroundColor Green
    Write-Host "Launch it from your Start Menu or Desktop shortcut.`n" -ForegroundColor Cyan
} else {
    # Bare .exe — just copy to a permanent place
    $installDir = Join-Path $env:LOCALAPPDATA "SpeedMonitor"
    New-Item -ItemType Directory -Force -Path $installDir | Out-Null
    $dest = Join-Path $installDir "SpeedMonitor.exe"
    Copy-Item -Path $tempPath -Destination $dest -Force

    # Add to PATH for current user
    $userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$installDir*") {
        [Environment]::SetEnvironmentVariable("PATH", "$userPath;$installDir", "User")
    }

    Write-Host "`n$appName $version installed to $installDir" -ForegroundColor Green
    Write-Host "Run 'SpeedMonitor' from any terminal, or find it at:`n  $dest`n" -ForegroundColor Cyan
}

# Cleanup
Remove-Item $tempPath -ErrorAction SilentlyContinue
