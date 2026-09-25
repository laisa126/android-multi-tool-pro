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

if os.path.isfile('bin/adb'):
    added_files.append(('bin/adb', 'bin'))
if os.path.isfile('bin/fastboot'):
    added_files.append(('bin/fastboot', 'bin'))
if os.path.isdir('bin/drivers'):
    added_files.append(('bin/drivers', 'bin/drivers'))
if os.path.isdir('assets'):
    added_files.append(('assets', 'assets'))
if os.path.isdir('web'):
    added_files.append(('web', 'web'))

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
        'core',
        'core.adb_engine',
        'core.fastboot_engine',
        'core.frp_engine',
        'core.mtk_engine',
        'core.qualcomm_engine',
        'core.samsung_modem',
        'core.root_engine',
        'core.efs_engine',
        'core.error_handler',
        'core.device_matrix',
        'core.device_profiles',
        'core.downloader',
        'core.workflow_guide',
        'core.payload_extractor',
        'core.scatter_flasher',
        'core.transsion_mdm',
        'core.spd_engine',
        'core.proinfo_engine',
        'core.meta_engine',
        'core.lk_patcher',
        'core.rom_maker'
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
    icon='assets/icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
