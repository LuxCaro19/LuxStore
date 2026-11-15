# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import os

block_cipher = None

# Recolectar datos y submódulos necesarios para Django y librerías
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
    ('fiadores/templates', 'fiadores/templates'),
    ('ventas/templates', 'ventas/templates'),
    ('luxstore.ico', '.'),
]

hidden_imports = [
    # Django Core & Contrib
    'django',
    'django.core',
    'django.core.management',
    'django.core.management.commands',
    'django.contrib.admin',
    'django.contrib.admin.apps',
    'django.contrib.auth',
    'django.contrib.auth.apps',
    'django.contrib.contenttypes',
    'django.contrib.contenttypes.apps',
    'django.contrib.sessions',
    'django.contrib.sessions.apps',
    'django.contrib.sessions.models',
    'django.contrib.messages',
    'django.contrib.messages.apps',
    'django.contrib.staticfiles',
    'django.contrib.staticfiles.apps',
    'django.template.defaulttags',
    'django.template.loader_tags',

    # SQLite backend
    'django.db.backends.sqlite3',
    'django.db.backends.sqlite3.base',
    'django.db.backends.sqlite3.client',
    'django.db.backends.sqlite3.creation',
    'django.db.backends.sqlite3.features',
    'django.db.backends.sqlite3.introspection',
    'django.db.backends.sqlite3.operations',
    'django.db.backends.sqlite3.schema',

    # Apps del proyecto LuxStore
    'config',
    'config.urls',
    'config.wsgi',
    'config.settings',
    'productos',
    'productos.apps',
    'productos.models',
    'productos.views',
    'productos.urls',
    'ventas',
    'ventas.apps',
    'ventas.models',
    'ventas.views',
    'ventas.urls',
    'ventas.templatetags',
    'ventas.templatetags.ventas_extras',
    'fiadores',
    'fiadores.apps',
    'fiadores.models',
    'fiadores.views',
    'fiadores.urls',
    'usuarios',
    'usuarios.apps',
    'usuarios.models',
    'usuarios.views',
    'usuarios.urls',
    'configuracion',
    'configuracion.apps',
    'configuracion.models',

    # Servidor y visor de escritorio
    'waitress',
    'webview',
    'webview.platforms.winforms',
    'clr_loader',
    'pythonnet',
    'openpyxl',
]

# Recolectar submódulos automáticos de las apps
for app in ['config', 'productos', 'ventas', 'fiadores', 'usuarios', 'configuracion']:
    hidden_imports.extend(collect_submodules(app))

a = Analysis(
    ['desktop.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='LuxStore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='luxstore.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='LuxStore',
)
