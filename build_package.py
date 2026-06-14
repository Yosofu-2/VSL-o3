"""
LitManager Build Orchestration Script
Builds backend, frontend, and launcher, then assembles the distribution package.
"""
import subprocess
import sys
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
DIST_DIR = PROJECT_ROOT / "dist_package"
BUILD_DIR = PROJECT_ROOT / "build_temp"


def run_command(cmd, cwd=None):
    """Run a command and check for errors."""
    print(f"\n>>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_ROOT)
    if result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        sys.exit(1)
    return result


def clean():
    """Clean previous build artifacts."""
    print("\n" + "="*60)
    print("CLEANING PREVIOUS BUILDS")
    print("="*60)

    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
            print(f"Removed: {d}")


def build_backend():
    """Build backend executable."""
    print("\n" + "="*60)
    print("BUILDING BACKEND (FastAPI Server)")
    print("="*60)

    run_command([
        sys.executable, "-m", "PyInstaller",
        "build_backend.spec",
        "--distpath", str(DIST_DIR / "backend"),
        "--workpath", str(BUILD_DIR / "backend"),
        "--noconfirm"
    ])

    print("✓ Backend build complete")


def build_frontend():
    """Build frontend executable."""
    print("\n" + "="*60)
    print("BUILDING FRONTEND (CustomTkinter GUI)")
    print("="*60)

    run_command([
        sys.executable, "-m", "PyInstaller",
        "build_frontend.spec",
        "--distpath", str(DIST_DIR / "frontend"),
        "--workpath", str(BUILD_DIR / "frontend"),
        "--noconfirm"
    ])

    print("✓ Frontend build complete")


def build_launcher():
    """Build launcher executable."""
    print("\n" + "="*60)
    print("BUILDING LAUNCHER")
    print("="*60)

    # Create launcher spec
    launcher_spec = '''
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    excludes=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LitManagerLauncher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    windowed=True,
    icon=None,
)
'''
    spec_path = PROJECT_ROOT / "build_launcher.spec"
    spec_path.write_text(launcher_spec, encoding="utf-8")

    run_command([
        sys.executable, "-m", "PyInstaller",
        "build_launcher.spec",
        "--distpath", str(DIST_DIR / "launcher"),
        "--workpath", str(BUILD_DIR / "launcher"),
        "--noconfirm"
    ])

    print("✓ Launcher build complete")


def assemble_package():
    """Assemble final distribution package."""
    print("\n" + "="*60)
    print("ASSEMBLING DISTRIBUTION PACKAGE")
    print("="*60)

    final_dir = DIST_DIR / "LitManager"
    if final_dir.exists():
        shutil.rmtree(final_dir)
    final_dir.mkdir(parents=True)

    # Copy executables
    shutil.copy2(DIST_DIR / "launcher" / "LitManagerLauncher.exe", final_dir / "LitManager.exe")
    shutil.copy2(DIST_DIR / "backend" / "LitManagerServer.exe", final_dir / "LitManagerServer.exe")

    # Create data directory
    (final_dir / "data").mkdir(exist_ok=True)

    # Calculate total size
    total_size = sum(f.stat().st_size for f in final_dir.rglob('*')) / 1024 / 1024

    print(f"\n✓ Package assembled at: {final_dir}")
    print(f"  Total size: {total_size:.1f} MB")
    print(f"\nContents:")
    for f in final_dir.iterdir():
        if f.is_file():
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"  - {f.name} ({size_mb:.1f} MB)")


def main():
    print("="*60)
    print("LitManager Build System")
    print("="*60)

    # Check PyInstaller
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("Installing PyInstaller...")
        run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

    clean()
    build_backend()
    build_frontend()
    build_launcher()
    assemble_package()

    print("\n" + "="*60)
    print("BUILD COMPLETE!")
    print("="*60)
    print(f"\nDistribution package: {DIST_DIR / 'LitManager'}")
    print("\nNext steps:")
    print("1. Test the package by running LitManager.exe")
    print("2. Create installer with Inno Setup (LitManager.iss)")
    print("3. Distribute the installer")


if __name__ == "__main__":
    main()
