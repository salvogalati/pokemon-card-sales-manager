import re
from PyQt5 import QtWidgets, QtGui
from config import get_resource_path



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