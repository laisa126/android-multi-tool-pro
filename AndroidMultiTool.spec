# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

added_files = [
    ('bin/adb.exe', 'bin'),
    ('bin/fastboot.exe', 'bin'),
    ('bin/AdbWinApi.dll', 'bin'),
    ('bin/AdbWinUsbApi.dll', 'bin'),
    ('bin/libwinpthread-1.dll', 'bin'),
    ('core', 'core')
]

# If on Linux or Mac during cross-inspection, include standard unix binaries as fallback
if os.path.isfile('bin/adb'):
    added_files.append(('bin/adb', 'bin'))
if os.path.isfile('bin/fastboot'):
    added_files.append(('bin/fastboot', 'bin'))

a = Analysis(
    ['app_gui.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'core.adb_engine',
        'core.fastboot_engine',
        'core.frp_engine',
        'core.device_profiles',
        'core.downloader'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
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
    name='AndroidMultiTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed GUI application (no command prompt window popping up)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
