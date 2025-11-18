# -*- mode: python ; coding: utf-8 -*-
import os
import sys

# 获取项目根目录（spec文件所在目录的父目录）
spec_dir = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(spec_dir)

block_cipher = None

a = Analysis(
    [os.path.join(project_root, 'app.py')],
    pathex=[project_root],
    binaries=[],
    datas=[
        (os.path.join(project_root, 'templates'), 'templates'),
    ] + ([(os.path.join(project_root, 'static'), 'static')] if os.path.exists(os.path.join(project_root, 'static')) and os.listdir(os.path.join(project_root, 'static')) else []),
    hiddenimports=[
        'eventlet',
        'flask_socketio',
        'engineio.async_drivers.eventlet',
        'engineio.async_drivers.threading',
        'socketio',
        'paramiko',
        'cryptography',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        'parse_share_link',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
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
    name='naspt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 显示控制台窗口，方便查看日志
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径，如 'icon.ico'
)

