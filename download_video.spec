# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

import nodejs_wheel.executable
import pytubefix
from PyInstaller.utils.hooks import collect_submodules

pytubefix_dir = Path(pytubefix.__file__).parent
node_root = Path(nodejs_wheel.executable.ROOT_DIR)
if os.name == "nt":
    node_binary = node_root / "node.exe"
    node_destination = "nodejs_wheel"
else:
    node_binary = node_root / "bin" / "node"
    node_destination = "nodejs_wheel/bin"

a = Analysis(
    ["download_video.py"],
    pathex=[],
    binaries=[(str(node_binary), node_destination)],
    datas=[
        (str(pytubefix_dir / "sig_nsig" / "vm" / "runner.js"), "pytubefix/sig_nsig/vm"),
        (str(pytubefix_dir / "botGuard" / "vm" / "botGuard.js"), "pytubefix/botGuard/vm"),
    ],
    hiddenimports=collect_submodules("pytubefix") + collect_submodules("aiohttp"),
    hookspath=[],
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
    name="download_video",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
