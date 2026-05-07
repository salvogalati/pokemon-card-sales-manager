a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ("main.ui", "."),
        ("style.qss", "."),
        ("icons", "icons"),
        ("backups", "backups"),
        ("pokemon.db", "."),
        ("card_database.db", "."),
        ("dialogs", "dialogs"),
        ("images", "images"),
        ("ui", "ui"),
    ],
    hiddenimports=[],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='main',
    console=True,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name='main',
)