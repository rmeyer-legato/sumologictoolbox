# -*- mode: python ; coding: utf-8 -*-
import PyInstaller.config
import os
import pkgutil

PyInstaller.config.CONF['distpath'] = "./dist/mac"
dateutil_path = os.path.dirname(pkgutil.get_loader("dateutil").path)
backports_path = os.path.dirname(pkgutil.get_loader("backports").path)

block_cipher = None

a = Analysis(['sumotoolbox.py'],
             binaries=[],
             datas=[( 'data/*', 'data' ),
                    ( 'qtmodern', 'qtmodern' ),
                    ( 'modules/*', 'modules' ),
                    (dateutil_path, 'dateutil'),
                    (backports_path, 'backports')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='sumotoolbox_mac',
          debug=False,
          strip=None,
          upx=True,
          console=False )
