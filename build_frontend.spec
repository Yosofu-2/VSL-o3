# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for LitManager Frontend (CustomTkinter GUI)"""

block_cipher = None

a = Analysis(
    ['modern_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('i18n.py', '.'),
        ('api_client.py', '.'),
        ('gui_utils.py', '.'),
        ('chart_widget.py', '.'),
        ('statistics_view.py', '.'),
        ('reader_gui.py', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.simpledialog',
        'matplotlib',
        'matplotlib.figure',
        'matplotlib.backends.backend_tkagg',
        'openpyxl',
        'requests',
        'httpx',
    ],
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
    name='LitManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    windowed=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
