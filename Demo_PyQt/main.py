import sys, re
from PyQt5 import QtWidgets, uic, QtSql, QtGui
from PyQt5.QtCore import Qt

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Carica il file .ui
        uic.loadUi("main.ui", self)
        
        # Connessione DB
        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName("../pokemon.db")

        if not self.db.open():
            print("Errore apertura DB", self.db.lastError().text())
            return

        # Modello
        self.model = QtSql.QSqlTableModel(self)
        self.model.setTable("stock")  # <-- cambia con la tua tabella
        self.model.select()

        # Collega alla tabella
        self.tableStock.setModel(self.model)
        self.tableStock.activated.connect(self.aggiungi_al_carrello)
        #self.tableStock.doubleClicked.connect(self.aggiungi_al_carrello)

        # Collegamento ricerca live
        self.lineEdit.textChanged.connect(self.filtra_tabella)
        self.lineEdit.returnPressed.connect(lambda: self.cerca_barcode(self.lineEdit.text()))

        self.button_svuota_carrello.clicked.connect(self.svuota_carrello)

        self.tableWidget_carrello.setColumnCount(5)
        self.tableWidget_carrello.setHorizontalHeaderLabels(["ID", "Nome", "Prezzo stock", "Prezzo di vendita", " "])
        self.tableWidget_carrello.itemChanged.connect(self.valida_prezzo)
        self.tableWidget_carrello.itemChanged.connect(self.salva_valore)
        self._old_value = {}

        #self.button_aggiungi_carta.clicked.connect(self.aggiungi_al_carrello)

        self.sconto_input.textChanged.connect(self.applica_sconto)

    def filtra_tabella(self, testo):
        if not testo:
            self.model.setFilter("")
            self.model.select()
            return
        testo_sicuro = self.pulisci_testo(testo)

        filtro = f"""
        id LIKE '%{testo_sicuro}%'
        OR nome_completo LIKE '%{testo_sicuro}%'
        """

        self.model.setFilter(filtro)
        self.model.select()

    def cerca_barcode(self, codice):
        codice = self.pulisci_testo(codice)

        filtro = f"id = '{codice}'"   # match ESATTO

        self.model.setFilter(filtro)
        self.model.select()

        if self.model.rowCount() == 1:
            self.tableStock.selectRow(0)
            self.aggiungi_al_carrello()
        else:
            msg = self.createMessageBox(
                "Non trovato",
                f"Codice {codice} non trovato",
                QtWidgets.QMessageBox.Warning
            )
            msg.exec_()

    def aggiungi_al_carrello(self):
        index = self.tableStock.currentIndex()
        if not index.isValid():
            return

        row = index.row()

        id_ = self.model.data(self.model.index(row, 0))
        nome = self.model.data(self.model.index(row, 1))
        prezzo = self.model.data(self.model.index(row, 2))
        stock = self.model.data(self.model.index(row, 3))
        stock_disponibile = int(stock)

        quantita_nel_carrello = 0

        for i in range(self.tableWidget_carrello.rowCount()):
            if self.tableWidget_carrello.item(i, 0).text() == str(id_):
                quantita_nel_carrello += 1

        if quantita_nel_carrello >= stock_disponibile:
            msg = self.createMessageBox(title="Stock esaurito", text="La carta è attualmente non disponibile.", icon=QtWidgets.QMessageBox.Warning)
            msg.exec_()
            return

        # controlla duplicati (opzionale)
        # for i in range(self.tableWidget_carrello.rowCount()):
        #     if self.tableWidget_carrello.item(i, 0).text() == str(id_):
        #         return

        # aggiungi nuova riga
        row_pos = self.tableWidget_carrello.rowCount()
        self.tableWidget_carrello.insertRow(row_pos)

        id_item = QtWidgets.QTableWidgetItem(str(id_))
        nome_item = QtWidgets.QTableWidgetItem(str(nome))
        prezzo_item = QtWidgets.QTableWidgetItem(str(prezzo))
        prezzo_vendita_item = QtWidgets.QTableWidgetItem(str(prezzo))
        # ID NON editabile
        id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Nome NON editabile
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo editabile
        #prezzo_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.tableWidget_carrello.setItem(row_pos, 0, id_item)
        self.tableWidget_carrello.setItem(row_pos, 1, nome_item)
        self.tableWidget_carrello.setItem(row_pos, 2, prezzo_item)
        self.tableWidget_carrello.setItem(row_pos, 3, prezzo_vendita_item)

        # ✔️ QUI va il bottone X
        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon("icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)

        self.tableWidget_carrello.setCellWidget(row_pos, 4, btn)

        self.aggiorna_totale()
        self.aggiorna_stock_visivo()

    def rimuovi_dal_carrello(self):
        row = self.tableWidget_carrello.currentRow()
        if row >= 0:
            self.tableWidget_carrello.removeRow(row)

        self.aggiorna_totale()
        self.aggiorna_stock_visivo()

    def rimuovi_riga_button(self):
        btn = self.sender()
        index = self.tableWidget_carrello.indexAt(btn.pos())
        row = index.row()

        self.tableWidget_carrello.removeRow(row)
        self.aggiorna_totale()
        self.aggiorna_stock_visivo()
        
    def svuota_carrello(self):
        self.tableWidget_carrello.setRowCount(0)
        self.aggiorna_totale()
        self.aggiorna_stock_visivo()

    def aggiorna_totale(self):
        totale = 0.0

        for row in range(self.tableWidget_carrello.rowCount()):
            item = self.tableWidget_carrello.item(row, 2)  # colonna prezzo
            if item is not None:
                try:
                    prezzo = float(item.text())
                    totale += prezzo
                except ValueError:
                    pass

        self.label_totale_carrello.setText(f"{totale:.2f} €")
        self.label_totale_dapagare.setText(f"{totale:.2f} €")
        if self.tableWidget_carrello.rowCount() > 0:
            self.button_svuota_carrello.setEnabled(True)
            self.sconto_input.setEnabled(True)
        else:
            self.button_svuota_carrello.setEnabled(False)
            self.sconto_input.setEnabled(False)

        if self.tableWidget_carrello.rowCount() > 0:    
            self.applica_sconto(self.sconto_input.text())

        

    def applica_sconto(self, testo):
        try:
            sconto = float(testo.replace(",", "."))
        except ValueError:
            sconto = 0.0
        totale = float(self.label_totale_carrello.text().replace(" €", ""))
        totale_scontato = totale - sconto
        sconto_per_riga = sconto / self.tableWidget_carrello.rowCount()
        self.label_totale_dapagare.setText(f"{totale_scontato:.2f} €")
        
        for row in range(self.tableWidget_carrello.rowCount()):
            prezzo_item = self.tableWidget_carrello.item(row, 2)  # colonna prezzo stock
            prezzo_scontato_item = self.tableWidget_carrello.item(row, 3)
            if prezzo_item is not None and prezzo_scontato_item is not None:
                try:
                    prezzo = float(prezzo_item.text())
                    if totale > 0:
                        prezzo_scontato = prezzo - (prezzo / totale) * sconto # sconto proporzionale
                        #prezzo_scontato = prezzo - sconto_per_riga # sconto uniforme
                        prezzo_scontato_item.setText(f"{prezzo_scontato:.2f}")
                except ValueError:
                    pass

    def valida_prezzo(self, item):
        colonna_prezzo = 2

        if item.column() != colonna_prezzo:
            return

        testo = item.text().replace(",", ".")

        try:
            float(testo)
            self.aggiorna_totale()
        except ValueError:
            # ripristina valore precedente
            old = self._old_value.get((item.row(), item.column()), "0")
            item.setText(old)

    def salva_valore(self, item):
        self._old_value[(item.row(), item.column())] = item.text()

    def aggiorna_stock_visivo(self):
        return
        for row in range(self.model.rowCount()):
            id_ = self.model.data(self.model.index(row, 0))
            stock_reale = int(self.model.data(self.model.index(row, 3)))

            # calcola quantità nel carrello
            qta = 0
            for i in range(self.tableWidget_carrello.rowCount()):
                if self.tableWidget_carrello.item(i, 0).text() == str(id_):
                    qta += 1

            stock_visibile = stock_reale - qta

            # aggiorna SOLO UI
            self.model.setData(self.model.index(row, 3), stock_visibile)

    def createMessageBox(self, title, text, icon=QtWidgets.QMessageBox.Information , buttons=[]):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        for button in buttons:
            msg.addButton(button)
        return msg

    def pulisci_testo(self, testo):
        testo_sicuro = re.sub(r"[^\w\s\-']", '', testo)
        return testo_sicuro.replace('%', r'\%').replace('_', r'\_')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    
    # Stylesheet moderno
    stylesheet = open("style.qss").read()
    
    app.setStyle('Fusion')
    app.setStyleSheet(stylesheet)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())