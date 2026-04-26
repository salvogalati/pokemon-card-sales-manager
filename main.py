import sys
import os
from PyQt5 import QtWidgets, uic, QtSql
from tabs.magazzino import MagazzinoTabController
from tabs.acquisti import AcquistiTabController
from tabs.vendite import VenditeTabController
from tabs.storico import StoricoTabController
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



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    # Stylesheet moderno
    stylesheet = open(get_resource_path("style.qss")).read()

    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())
