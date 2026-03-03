# -*- mode: python ; coding: utf-8 -*-
import PyInstaller.config
from PyInstaller.utils.hooks import collect_all

PyInstaller.config.CONF['distpath'] = "dist\\windows"

datas = [
    ('data/*', 'data'),
    ('qtmodern', 'qtmodern'),
    ('modules/*', 'modules'),
]
hiddenimports = []
binaries = []
tmp_ret = collect_all('tzdata')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['sumotoolbox.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='sumotoolbox_windows',
    debug=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
)
