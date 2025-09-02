# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('./assets', 'assets'), ('./licenses', 'licenses'), ('./translations', 'translations')],
    hiddenimports=['win32console', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'pyqtgraph', 'shiboken6', 'odrive.fibre'],
    hookspath=['./hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ODrive GUI Configurador',
    debug=False,
    bootloader_ignore_signals=False,
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
    icon=['assets\\odrive_icon.ico'],
)
