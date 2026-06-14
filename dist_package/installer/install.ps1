
# LitManager Installer
# This script installs LitManager to the user's Program Files directory

param(
    [switch]$Silent,
    [string]$InstallPath
)

$AppName = "LitManager"
$AppVersion = "2.0.0"
$Publisher = "LitManager Team"

# Default installation path
if (-not $InstallPath) {
    $InstallPath = Join-Path $env:LOCALAPPDATA $AppName
}

Write-Host "Installing $AppName v$AppVersion..." -ForegroundColor Green
Write-Host "Installation path: $InstallPath" -ForegroundColor Cyan

# Create installation directory
if (Test-Path $InstallPath) {
    Write-Host "Removing previous installation..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $InstallPath
}

New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $InstallPath "data") | Out-Null

# Copy files
$SourceDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Files = Get-ChildItem -Path $SourceDir -File

foreach ($File in $Files) {
    if ($File.Name -ne "install.ps1") {
        Write-Host "Copying $($File.Name)..."
        Copy-Item -Path $File.FullName -Destination $InstallPath -Force
    }
}

# Create Start Menu shortcut
$StartMenuPath = [Environment]::GetFolderPath('Programs')
$ShortcutPath = Join-Path $StartMenuPath "$AppName.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $InstallPath "LitManager.exe"
$Shortcut.WorkingDirectory = $InstallPath
$Shortcut.Description = "$AppName v$AppVersion"
$Shortcut.Save()

# Create Desktop shortcut (optional)
if (-not $Silent) {
    $DesktopPath = [Environment]::GetFolderPath('Desktop')
    $DesktopShortcut = Join-Path $DesktopPath "$AppName.lnk"
    $DesktopLink = $WshShell.CreateShortcut($DesktopShortcut)
    $DesktopLink.TargetPath = Join-Path $InstallPath "LitManager.exe"
    $DesktopLink.WorkingDirectory = $InstallPath
    $DesktopLink.Description = "$AppName v$AppVersion"
    $DesktopLink.Save()
}

# Create uninstaller
$UninstallScript = @'
@echo off
echo Uninstalling LitManager...
if exist "%LOCALAPPDATA%\LitManager" (
    rmdir /s /q "%LOCALAPPDATA%\LitManager"
    echo LitManager uninstalled successfully.
) else (
    echo LitManager is not installed.
)
pause
'@

$UninstallPath = Join-Path $InstallPath "uninstall.bat"
Set-Content -Path $UninstallPath -Value $UninstallScript -Encoding ASCII

# Create uninstaller shortcut
$UninstallShortcut = Join-Path $StartMenuPath "Uninstall $AppName.lnk"
$UninstallLink = $WshShell.CreateShortcut($UninstallShortcut)
$UninstallLink.TargetPath = $UninstallPath
$UninstallLink.WorkingDirectory = $InstallPath
$UninstallLink.Description = "Uninstall $AppName"
$UninstallLink.Save()

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host "LitManager has been installed to: $InstallPath" -ForegroundColor Cyan
Write-Host ""

if (-not $Silent) {
    $Launch = Read-Host "Would you like to launch LitManager now? (Y/N)"
    if ($Launch -eq 'Y' -or $Launch -eq 'y') {
        Start-Process (Join-Path $InstallPath "LitManager.exe")
    }
}
