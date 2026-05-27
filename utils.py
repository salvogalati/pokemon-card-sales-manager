import hashlib
import re
from PyQt5 import QtWidgets, QtGui
from config import get_resource_path
from PyQt5.QtCore import Qt


def pulisci_testo(testo):
    testo_sicuro = re.sub(r"[^\w\s\-']", "", testo)
    return testo_sicuro.replace("%", r"\%").replace("_", r"\_")


def createMessageBox(title, text, icon=QtWidgets.QMessageBox.Information, buttons=[]):
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.setWindowIcon(QtGui.QIcon(get_resource_path("icons/logo_kingdom_cards.png")))
    for button in buttons:
        msg.addButton(button)
    return msg


def get_column_index(table, column_name):
    for i in range(table.columnCount()):
        header = table.horizontalHeaderItem(i)
        if header and header.text() == column_name:
            return i
    return -1


def generate_barcode(nome, espansione, condizione):
    def clean(s):
        return re.sub(r"[^A-Z0-9]", "", s.upper())

    # parte leggibile
    base = f"{clean(nome)[:4]}-{clean(espansione)[:3]}-{clean(condizione)[:2]}"

    # hash deterministico
    raw = f"{nome}|{espansione}|{condizione}".upper()
    short_hash = hashlib.md5(raw.encode()).hexdigest()[:6].upper()

    return f"{base}-{short_hash}"

def auto_size_table_columns(table, padding=30):
    header = table.horizontalHeader()
    font_metrics = header.fontMetrics()

    for col in range(table.model().columnCount()):
        text = table.model().headerData(col, Qt.Horizontal)
        width = font_metrics.horizontalAdvance(str(text)) + padding
        table.setColumnWidth(col, width)