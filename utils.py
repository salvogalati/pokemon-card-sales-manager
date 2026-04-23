import re
from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QTableView
from PyQt5.QtSql import QSqlQuery, QSqlTableModel, QSqlDatabase

def pulisci_testo(testo):
    testo_sicuro = re.sub(r"[^\w\s\-']", '', testo)
    return testo_sicuro.replace('%', r'\%').replace('_', r'\_')

def createMessageBox(title, text, icon=QtWidgets.QMessageBox.Information , buttons=[]):
    msg = QtWidgets.QMessageBox()
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(icon)
    msg.setWindowIcon(QtGui.QIcon("icons/logo_kingdom_cards.png"))
    for button in buttons:
        msg.addButton(button)
    return msg