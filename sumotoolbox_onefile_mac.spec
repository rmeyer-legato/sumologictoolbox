# -*- mode: python ; coding: utf-8 -*-
import PyInstaller.config

PyInstaller.config.CONF['distpath'] = "./dist/mac"

a = Analysis(
    ['sumotoolbox.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/*', 'data'),
        ('qtmodern', 'qtmodern'),
        ('modules/*', 'modules'),
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
