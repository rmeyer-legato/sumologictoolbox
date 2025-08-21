# -*- mode: python ; coding: utf-8 -*-

import PyInstaller.config
import os
import pkgutil

PyInstaller.config.CONF['distpath'] = "./dist/mac"
dateutil_path = os.path.dirname(pkgutil.get_loader("dateutil").path)

block_cipher = None

a = Analysis(
    ['sumotoolbox.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/*', 'data'),
        ('qtmodern', 'qtmodern'),
        ('modules/*', 'modules'),
        (dateutil_path, 'dateutil')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    name='sumotoolbox_mac',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
