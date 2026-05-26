# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path(SPECPATH).parents[1]
src_root = project_root / "src"

datas = collect_data_files("fratelanza")
datas += [
    (str(project_root / "config" / "app.toml"), "config"),
    (str(project_root / ".env.example"), "."),
]


a = Analysis(
    [str(src_root / "fratelanza" / "main.py")],
    pathex=[str(src_root), str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
    ],
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
    [],
    exclude_binaries=True,
    name="FratelanzaBusinessSuite",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FratelanzaBusinessSuite",
)
