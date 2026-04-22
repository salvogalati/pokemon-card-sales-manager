import sys, re
from PyQt5 import QtWidgets, uic, QtSql, QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from tabs.magazzino import MagazzinoTabController

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

        self.tableWidget_carrello.setColumnCount(6)
        self.tableWidget_carrello.setHorizontalHeaderLabels(["Barcode","Espansione", "Nome", "Prezzo stock", "Prezzo di vendita", " "])
        self.tableWidget_carrello.setColumnHidden(0, True)
        #self.tableWidget_carrello.itemChanged.connect(self.valida_prezzo)
        #self.tableWidget_carrello.itemChanged.connect(self.salva_valore)
        self._old_value = {}

        #self.button_aggiungi_carta.clicked.connect(self.aggiungi_al_carrello)

        self.sconto_input.textChanged.connect(self.applica_sconto)
        self.button_concludi_vendita.clicked.connect(self.concludi_vendita)

        self.tab_magazzino_controller = MagazzinoTabController(self)


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

        barcode = self.model.data(self.model.index(row, 0))
        espansione = self.model.data(self.model.index(row, 1))
        nome = self.model.data(self.model.index(row, 2))
        prezzo = self.model.data(self.model.index(row, 3))
        stock = self.model.data(self.model.index(row, 4))
        stock_disponibile = int(stock)

        quantita_nel_carrello = 0

        for i in range(self.tableWidget_carrello.rowCount()):
            if self.tableWidget_carrello.item(i, 0).text() == str(barcode):
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
        barcode_item = QtWidgets.QTableWidgetItem(str(barcode))
        espansione_item = QtWidgets.QTableWidgetItem(str(espansione))
        nome_item = QtWidgets.QTableWidgetItem(str(nome))
        prezzo_item = QtWidgets.QTableWidgetItem(str(prezzo))
        prezzo_vendita_item = QtWidgets.QTableWidgetItem(str(prezzo))
        # ID NON editabile
        barcode_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Nome NON editabile
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo editabile
        #prezzo_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.tableWidget_carrello.setItem(row_pos, 0, barcode_item)
        self.tableWidget_carrello.setItem(row_pos, 1, espansione_item)
        self.tableWidget_carrello.setItem(row_pos, 2, nome_item)
        self.tableWidget_carrello.setItem(row_pos, 3, prezzo_item)
        self.tableWidget_carrello.setItem(row_pos, 4, prezzo_vendita_item)

        # ✔️ QUI va il bottone X
        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon("icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)

        self.tableWidget_carrello.setCellWidget(row_pos, 5, btn)

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
            item = self.tableWidget_carrello.item(row, 4)  # colonna prezzo
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
            self.button_concludi_vendita.setEnabled(True)
        else:
            self.button_svuota_carrello.setEnabled(False)
            self.sconto_input.setEnabled(False)
            self.button_concludi_vendita.setEnabled(False)

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
            prezzo_item = self.tableWidget_carrello.item(row, 3)  # colonna prezzo stock
            prezzo_scontato_item = self.tableWidget_carrello.item(row, 4)
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

    def concludi_vendita(self):
        if self.tableWidget_carrello.rowCount() == 0:
            return


        # 🔒 inizio transazione
        self.db.transaction()

        try:
            for row in range(self.tableWidget_carrello.rowCount()):
                barcode = self.tableWidget_carrello.item(row, 0).text()
                espansione = self.tableWidget_carrello.item(row, 1).text()
                nome = self.tableWidget_carrello.item(row, 2).text()
                prezzo_stock = float(self.tableWidget_carrello.item(row, 3).text())
                prezzo_vendita = float(self.tableWidget_carrello.item(row, 4).text())
                sell_date = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

                # INSERT vendita
                insert_query = QtSql.QSqlQuery()
                insert_query.prepare("""
                    INSERT INTO sell (barcode, espansione, nome, prezzo_stock, prezzo_vendita, sell_date)
                    VALUES (:barcode, :espansione, :nome, :ps, :pv, :date)
                """)

                insert_query.bindValue(":barcode", barcode)
                insert_query.bindValue(":espansione", espansione)
                insert_query.bindValue(":nome", nome)
                insert_query.bindValue(":ps", prezzo_stock)
                insert_query.bindValue(":pv", prezzo_vendita)
                insert_query.bindValue(":date", sell_date)
                if not insert_query.exec_():
                    raise Exception(insert_query.lastError().text())

                # UPDATE stock
                update_query = QtSql.QSqlQuery()
                update_query.prepare("UPDATE stock SET quantita_stock = quantita_stock - 1 WHERE barcode = ?")
                update_query.addBindValue(barcode)
                if not update_query.exec_():
                    raise Exception(update_query.lastError().text())

            # ✅ commit UNA SOLA VOLTA
            self.db.commit()

        except Exception as e:
            # ❌ rollback totale
            self.db.rollback()

            msg = self.createMessageBox(
                "Errore",
                f"Errore durante la vendita:\n{str(e)}",
                QtWidgets.QMessageBox.Critical
            )
            msg.exec_()
            import traceback
            traceback.print_exc()
            return

        # 🔄 refresh dati
        self.model.select()

        msg = self.createMessageBox(
            "Vendita conclusa",
            "La vendita è stata registrata con successo!",
            QtWidgets.QMessageBox.Information,
        )
        msg.exec_()

        self.svuota_carrello()

    def createMessageBox(self, title, text, icon=QtWidgets.QMessageBox.Information , buttons=[]):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setWindowIcon(QtGui.QIcon("icons/logo_kingdom_cards.png"))
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