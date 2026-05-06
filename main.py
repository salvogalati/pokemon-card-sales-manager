import sys
import os
import traceback
from PyQt5 import QtWidgets, uic, QtSql
from tabs.magazzino import MagazzinoTabController
from tabs.acquisti import AcquistiTabController
from tabs.vendite import VenditeTabController
from tabs.storico import StoricoTabController
from tabs.database import DatabaseTabController
from config import main_db, card_db, get_resource_path


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Carica il file .ui
        uic.loadUi(get_resource_path("main.ui"), self)

        # Connessione DB
        self.db_main = QtSql.QSqlDatabase.addDatabase("QSQLITE", "main_connection")
        self.db_main.setDatabaseName(get_resource_path(main_db))
        self.db_main.open()

        self.db_cards = QtSql.QSqlDatabase.addDatabase("QSQLITE", "card_db_connection")
        self.db_cards.setDatabaseName(get_resource_path(card_db))
        self.db_cards.open()

        if not self.db_main.isOpen() or not self.db_cards.isOpen():
            print("Errore apertura DB", self.db_main.lastError().text())
            print("Errore apertura DB cards", self.db_cards.lastError().text())
            return

        self.tab_magazzino_controller = MagazzinoTabController(self)
        self.tabAcquisti = AcquistiTabController(self)
        self.tabVendite = VenditeTabController(self)
        self.tabStorico = StoricoTabController(self)
        self.tabDatabase = DatabaseTabController(self)

        self.adjustSize()

class ErrorDialog(QtWidgets.QDialog):
    def __init__(self, error_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Errore inatteso")
        self.resize(700, 500)

        layout = QtWidgets.QVBoxLayout(self)

        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setPlainText(error_text)

        layout.addWidget(self.text)

        btn = QtWidgets.QPushButton("Chiudi")
        btn.clicked.connect(self.close)
        layout.addWidget(btn)

def qt_exception_hook(type, value, tb):
    sys.__excepthook__(type, value, tb)
    show_exception_box(type, value, tb)

def show_exception_box(exc_type, exc_value, exc_traceback):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    try:
        app = QtWidgets.QApplication.instance()
        if app:
            dlg = ErrorDialog(msg)
            dlg.exec_()
        else:
            print(msg)
    except:
        print(msg)


if __name__ == "__main__":
    sys.excepthook = qt_exception_hook
    app = QtWidgets.QApplication(sys.argv)

    # Stylesheet moderno
    stylesheet = open(get_resource_path("style.qss")).read()

    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
