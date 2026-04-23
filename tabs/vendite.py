from datetime import datetime
import traceback

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QTableView
from PyQt5.QtSql import QSqlQuery, QSqlTableModel, QSqlDatabase
from .models.card_database_model import CardDatabaseModel
from utils import pulisci_testo, createMessageBox

from icons import icons_rc



class VenditeTabController(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

        
        db_main = QtSql.QSqlDatabase.database("main_connection")
        self.db_main = db_main  # Assign the main database connection to self.db_main
        self.model = QtSql.QSqlTableModel(None, self.db_main)
        self.model.setTable("stock")  # <-- cambia con la tua tabella
        self.model.select()
        
        # Collega alla tabella
        self.ui.tableStock.setModel(self.model)
        self.ui.tableStock.setColumnHidden(6, True)
        self.ui.tableStock.setColumnHidden(7, True)

        self.ui.tableStock.activated.connect(self.aggiungi_al_carrello)
        #self.ui.tableStock.doubleClicked.connect(self.aggiungi_al_carrello)
    
        # Collegamento ricerca live
        self.ui.lineEdit.textChanged.connect(self.filtra_tabella)
        self.ui.lineEdit.returnPressed.connect(lambda: self.cerca_barcode(self.ui.lineEdit.text()))

        self.ui.button_svuota_carrello.clicked.connect(self.svuota_carrello)

        self.ui.tableWidget_carrello.setColumnCount(7)
        self.ui.tableWidget_carrello.setHorizontalHeaderLabels(["Barcode","Espansione",
                    "Nome", "Condizione", "Prezzo stock", "Prezzo di vendita", " "])
        self.ui.tableWidget_carrello.setColumnHidden(0, True)
        #self.ui.tableWidget_carrello.itemChanged.connect(self.valida_prezzo)
        #self.ui.tableWidget_carrello.itemChanged.connect(self.salva_valore)

        self._old_value = {}

        #self.button_aggiungi_carta.clicked.connect(self.aggiungi_al_carrello)

        self.ui.sconto_input.textChanged.connect(self.applica_sconto)
        self.ui.button_concludi_vendita.clicked.connect(self.concludi_vendita)


    def filtra_tabella(self, testo):
        if not testo:
            self.model.setFilter("")
            self.model.select()
            return
        testo_sicuro = pulisci_testo(testo)

        filtro = f"""
        espansione LIKE '%{testo_sicuro}%'
        OR nome LIKE '%{testo_sicuro}%'
        OR barcode LIKE '%{testo_sicuro}%'
        """

        self.model.setFilter(filtro)
        self.model.select()

    def cerca_barcode(self, codice):
        codice = pulisci_testo(codice)

        filtro = f"barcode = '{codice}'"   # match ESATTO

        self.model.setFilter(filtro)
        self.model.select()

        if self.model.rowCount() == 1:
            self.ui.tableStock.selectRow(0)
            self.aggiungi_al_carrello()
        else:
            msg = createMessageBox(
                "Non trovato",
                f"Codice {codice} non trovato",
                QtWidgets.QMessageBox.Warning
            )
            msg.exec_()

    def aggiungi_al_carrello(self):
        index = self.ui.tableStock.currentIndex()
        if not index.isValid():
            return

        row = index.row()

        barcode = self.model.data(self.model.index(row, 0))
        espansione = self.model.data(self.model.index(row, 1))
        nome = self.model.data(self.model.index(row, 2))
        condizione = self.model.data(self.model.index(row, 3))
        prezzo_stock = self.model.data(self.model.index(row, 4))
        quantita_stock = self.model.data(self.model.index(row, 5))
        stock_disponibile = int(quantita_stock)

        quantita_nel_carrello = 0

        for i in range(self.ui.tableWidget_carrello.rowCount()):
            if self.ui.tableWidget_carrello.item(i, 0).text() == str(barcode):
                quantita_nel_carrello += 1

        if quantita_nel_carrello >= stock_disponibile:
            msg = createMessageBox(title="Stock esaurito", text="La carta è attualmente non disponibile.", icon=QtWidgets.QMessageBox.Warning)
            msg.exec_()
            return

        # controlla duplicati (opzionale)
        # for i in range(self.ui.tableWidget_carrello.rowCount()):
        #     if self.ui.tableWidget_carrello.item(i, 0).text() == str(id_):
        #         return

        # aggiungi nuova riga
        row_pos = self.ui.tableWidget_carrello.rowCount()
        self.ui.tableWidget_carrello.insertRow(row_pos)
        barcode_item = QtWidgets.QTableWidgetItem(str(barcode))
        espansione_item = QtWidgets.QTableWidgetItem(str(espansione))
        nome_item = QtWidgets.QTableWidgetItem(str(nome))
        condizione_item = QtWidgets.QTableWidgetItem(str(condizione))
        prezzo_item = QtWidgets.QTableWidgetItem(str(prezzo_stock))
        prezzo_vendita_item = QtWidgets.QTableWidgetItem(str(prezzo_stock))
        # ID NON editabile
        barcode_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Nome NON editabile
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo editabile
        #prezzo_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.ui.tableWidget_carrello.setItem(row_pos, 0, barcode_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 1, espansione_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 2, nome_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 3, condizione_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 4, prezzo_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 5, prezzo_vendita_item)

        # Pulsante rimuovi
        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon("icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)
        self.ui.tableWidget_carrello.setCellWidget(row_pos, 6, btn)

        self.aggiorna_totale()
        self.aggiorna_stock_visivo()
  
    def rimuovi_dal_carrello(self):
        row = self.ui.tableWidget_carrello.currentRow()
        if row >= 0:
            self.ui.tableWidget_carrello.removeRow(row)

        self.aggiorna_totale()
        self.aggiorna_stock_visivo()

    def rimuovi_riga_button(self):
        btn = self.sender()
        if not btn:
            return

        for row in range(self.ui.tableWidget_carrello.rowCount()):
            if self.ui.tableWidget_carrello.cellWidget(row, 6) == btn:
                self.ui.tableWidget_carrello.removeRow(row)
                break

        self.aggiorna_totale()
        self.aggiorna_stock_visivo()
        
    def svuota_carrello(self):
        self.ui.tableWidget_carrello.setRowCount(0)
        self.aggiorna_totale()
        self.aggiorna_stock_visivo()


    def aggiorna_totale(self):
        totale = 0.0

        for row in range(self.ui.tableWidget_carrello.rowCount()):
            item = self.ui.tableWidget_carrello.item(row, 4)  # colonna prezzo
            if item is not None:
                try:
                    prezzo = float(item.text())
                    totale += prezzo
                except ValueError:
                    pass

        self.ui.label_totale_carrello.setText(f"{totale:.2f} €")
        self.ui.label_totale_dapagare.setText(f"{totale:.2f} €")
        if self.ui.tableWidget_carrello.rowCount() > 0:
            self.ui.button_svuota_carrello.setEnabled(True)
            self.ui.sconto_input.setEnabled(True)
            self.ui.button_concludi_vendita.setEnabled(True)
        else:
            self.ui.button_svuota_carrello.setEnabled(False)
            self.ui.sconto_input.setEnabled(False)
            self.ui.button_concludi_vendita.setEnabled(False)

        if self.ui.tableWidget_carrello.rowCount() > 0:    
            self.applica_sconto(self.ui.sconto_input.text())

    def applica_sconto(self, testo):
        try:
            sconto = float(testo.replace(",", "."))
        except ValueError:
            sconto = 0.0
        totale = float(self.ui.label_totale_carrello.text().replace(" €", ""))
        totale_scontato = totale - sconto
        #sconto_per_riga = sconto / self.ui.tableWidget_carrello.rowCount()
        self.ui.label_totale_dapagare.setText(f"{totale_scontato:.2f} €")
        
        for row in range(self.ui.tableWidget_carrello.rowCount()):
            prezzo_item = self.ui.tableWidget_carrello.item(row, 4)  # colonna prezzo stock
            prezzo_scontato_item = self.ui.tableWidget_carrello.item(row, 5)
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
        if self.ui.tableWidget_carrello.rowCount() == 0:
            return


        # 🔒 inizio transazione
        self.db_main.transaction()

        try:
            for row in range(self.ui.tableWidget_carrello.rowCount()):
                barcode = self.ui.tableWidget_carrello.item(row, 0).text()
                espansione = self.ui.tableWidget_carrello.item(row, 1).text()
                nome = self.ui.tableWidget_carrello.item(row, 2).text()
                condizione = self.ui.tableWidget_carrello.item(row, 3).text()
                prezzo_stock = float(self.ui.tableWidget_carrello.item(row, 4).text())
                prezzo_vendita = float(self.ui.tableWidget_carrello.item(row, 5).text())
                sell_date = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

                # INSERT vendita
                insert_query = QtSql.QSqlQuery(self.db_main)
                insert_query.prepare("""
                    INSERT INTO sales (barcode, espansione, nome, condizione, prezzo_stock, prezzo_vendita, sell_date)
                    VALUES (:barcode, :espansione, :nome, :condizione, :ps, :pv, :date)
                """)

                insert_query.bindValue(":barcode", barcode)
                insert_query.bindValue(":espansione", espansione)
                insert_query.bindValue(":nome", nome)
                insert_query.bindValue(":condizione", condizione)
                insert_query.bindValue(":ps", prezzo_stock)
                insert_query.bindValue(":pv", prezzo_vendita)
                insert_query.bindValue(":date", sell_date)
                if not insert_query.exec_():
                    raise Exception(insert_query.lastError().text())

                # UPDATE stock
                update_query = QtSql.QSqlQuery(self.db_main)
                update_query.prepare("UPDATE stock SET quantita_stock = quantita_stock - 1 WHERE barcode = ?")
                update_query.addBindValue(barcode)
                if not update_query.exec_():
                    raise Exception(update_query.lastError().text())

            
            self.db_main.commit()

        except Exception as e:
            # ❌ rollback totale
            self.db_main.rollback()

            msg = createMessageBox(
                "Errore",
                f"Errore durante la vendita:\n{str(e)}",
                QtWidgets.QMessageBox.Critical
            )
            msg.exec_()
            traceback.print_exc()
            return

        # 🔄 refresh dati
        self.model.select()

        msg = createMessageBox(
            "Vendita conclusa",
            "La vendita è stata registrata con successo!",
            QtWidgets.QMessageBox.Information,
        )
        msg.exec_()

        self.svuota_carrello()