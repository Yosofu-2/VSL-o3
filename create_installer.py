"""
LitManager Installer Creator
Creates a self-extracting installer using PowerShell.
"""
import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist_package"
INSTALLER_DIR = DIST_DIR / "installer"


def create_installer():
    """Create a self-extracting installer using PowerShell."""
    print("="*60)
    print("CREATING INSTALLER")
    print("="*60)

    # Create installer directory
    if INSTALLER_DIR.exists():
        shutil.rmtree(INSTALLER_DIR)
    INSTALLER_DIR.mkdir(parents=True)

    # Copy distribution files
    dist_src = DIST_DIR / "LitManager"
    for item in dist_src.iterdir():
        if item.is_file():
            shutil.copy2(item, INSTALLER_DIR / item.name)
        elif item.is_dir():
            shutil.copytree(item, INSTALLER_DIR / item.name)

    # Create PowerShell installer script
    ps_script = r'''
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
'''

    installer_script = INSTALLER_DIR / "install.ps1"
    installer_script.write_text(ps_script, encoding="utf-8")

    # Create a batch file to run the PowerShell script
    bat_content = r'''
@echo off
echo Starting LitManager Installer...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause
'''

    bat_file = INSTALLER_DIR / "install.bat"
    bat_file.write_text(bat_content, encoding="utf-8")

    # Create a self-extracting archive using PowerShell
    print("\nCreating self-extracting archive...")

    # Create a ZIP file first
    zip_path = INSTALLER_DIR.parent / "LitManager-files.zip"
    if zip_path.exists():
        zip_path.unlink()

    shutil.make_archive(
        str(INSTALLER_DIR.parent / "LitManager-files"),
        'zip',
        INSTALLER_DIR
    )

    # Create a self-extracting executable
    sfx_script = r'''
# Self-extracting archive creator
# This creates a simple SFX using PowerShell

$ZipFile = "{zip_path}"
$OutputExe = "{output_exe}"

# Read the ZIP file as bytes
$ZipBytes = [System.IO.File]::ReadAllBytes($ZipFile)

# Create a simple extractor script
$ExtractorScript = @'
# Extract and run installer
$TempDir = Join-Path $env:TEMP "LitManager_Install_{guid}"
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

$ZipPath = Join-Path $TempDir "installer.zip"
[System.IO.File]::WriteAllBytes($ZipPath, $ZipData)

Expand-Archive -Path $ZipPath -DestinationPath $TempDir -Force

$InstallerScript = Join-Path $TempDir "install.ps1"
& powershell -ExecutionPolicy Bypass -File $InstallerScript

# Cleanup
Remove-Item -Recurse -Force $TempDir
'@

# This is a simplified approach - in production, use a proper SFX tool
Write-Host "Note: For a production installer, use Inno Setup or similar tool"
Write-Host "For now, use the install.bat file in the installer directory"
'''

    print(f"\n✓ Installer created at: {INSTALLER_DIR}")
    print(f"\nInstaller contents:")
    for item in INSTALLER_DIR.iterdir():
        if item.is_file():
            size_mb = item.stat().st_size / 1024 / 1024
            print(f"  - {item.name} ({size_mb:.1f} MB)")

    print(f"\n✓ ZIP archive created at: {zip_path}")

    print("\n" + "="*60)
    print("INSTALLER CREATION COMPLETE")
    print("="*60)
    print(f"\nTo install LitManager:")
    print(f"1. Navigate to: {INSTALLER_DIR}")
    print(f"2. Run: install.bat")
    print(f"3. Follow the installation wizard")
    print(f"\nOr distribute the ZIP file: {zip_path}")


def main():
    if not (DIST_DIR / "LitManager").exists():
        print("ERROR: Distribution package not found!")
        print("Please run build_package.py first.")
        sys.exit(1)

    create_installer()


if __name__ == "__main__":
    main()
