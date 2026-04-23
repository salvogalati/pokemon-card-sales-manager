import sys, re
from PyQt5 import QtWidgets, uic, QtSql, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from tabs.magazzino import MagazzinoTabController
from tabs.acquisti import AcquistiTabController
from tabs.vendite import VenditeTabController

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Carica il file .ui
        uic.loadUi("main.ui", self)
        
        # Connessione DB
        self.db_main = QtSql.QSqlDatabase.addDatabase("QSQLITE", "main_connection")
        self.db_main.setDatabaseName("../pokemon.db")
        self.db_main.open()

        self.db_cards = QtSql.QSqlDatabase.addDatabase("QSQLITE", "card_db_connection")
        self.db_cards.setDatabaseName("../card_database.db")
        self.db_cards.open()

        if not self.db_main.isOpen() or not self.db_cards.isOpen():
            print("Errore apertura DB", self.db_main.lastError().text())
            print("Errore apertura DB cards", self.db_cards.lastError().text())
            return

        self.tab_magazzino_controller = MagazzinoTabController(self)
        self.tabAcquisti = AcquistiTabController(self)
        self.tabVendite = VenditeTabController(self)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Stylesheet moderno
    stylesheet = open("style.qss").read()
    
    app.setStyle('Fusion')
    app.setStyleSheet(stylesheet)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())