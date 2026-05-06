import traceback

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt, QSize
from utils import pulisci_testo, createMessageBox
from .models.card_database_model import CardDatabaseModel
from config import stock_table
from utils import get_column_index
from icons import icons  # noqa: F401


class VenditeTabController(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

        db_main = QtSql.QSqlDatabase.database("main_connection")
        self.db_main = db_main  # Assign the main database connection to self.db_main
        #self.model = QtSql.QSqlTableModel(None, self.db_main)
        self.model = CardDatabaseModel(db_main)
        self.model.setTable(stock_table)  # <-- cambia con la tua tabella
        #self.model.setFilter("quantita_stock > 0")
        self.model.select()

        # Collega alla tabella
        self.ui.tableStock.setModel(self.model)
        self.ui.tableStock.hideColumn(self.model.fieldIndex("prezzo_acquisto"))
        self.ui.tableStock.hideColumn(self.model.fieldIndex("id"))
        self.ui.tableStock.activated.connect(self.aggiungi_al_carrello)
        self.ui.tableStock.setIconSize(QSize(60, 60))
        # self.ui.tableStock.doubleClicked.connect(self.aggiungi_al_carrello)

        # Collegamento ricerca live
        self.ui.lineEdit.textChanged.connect(self.filtra_tabella)
        self.ui.lineEdit.returnPressed.connect(
            lambda: self.cerca_barcode(self.ui.lineEdit.text())
        )

        self.ui.button_svuota_carrello.clicked.connect(self.svuota_carrello)

        self.ui.tableWidget_carrello.setColumnCount(8)
        self.ui.tableWidget_carrello.setHorizontalHeaderLabels(
            [
                "Barcode",
                "Nome",
                "ID Espansione",
                "Nome Espansione",
                "Condizione",
                "Prezzo stock",
                "Prezzo di vendita",
                " ",
            ]
        )
        self.ui.tableWidget_carrello.setColumnHidden(0, True)
        # self.ui.tableWidget_carrello.itemChanged.connect(self.valida_prezzo)
        # self.ui.tableWidget_carrello.itemChanged.connect(self.salva_valore)

        self._old_value = {}

        # self.button_aggiungi_carta.clicked.connect(self.aggiungi_al_carrello)

        self.ui.sconto_input.textChanged.connect(self.applica_sconto)
        self.ui.button_concludi_vendita.clicked.connect(self.concludi_vendita)

    def filtra_tabella(self, testo):
        if not testo:
            self.model.setFilter("")
            self.model.select()
            return
        testo_sicuro = pulisci_testo(testo)

        filtro = f"""
        espansione_id LIKE '%{testo_sicuro}%'
        OR espansione_nome LIKE '%{testo_sicuro}%'
        OR name LIKE '%{testo_sicuro}%'
        OR barcode LIKE '%{testo_sicuro}%'
        OR condizione LIKE '%{testo_sicuro}%'
        AND quantita_stock > 0
        """

        self.model.setFilter(filtro)
        self.model.select()

    def cerca_barcode(self, codice):
        codice = pulisci_testo(codice)

        filtro = f"barcode = '{codice}'"  # match ESATTO

        self.model.setFilter(filtro)
        self.model.select()

        if self.model.rowCount() == 1:
            self.ui.tableStock.selectRow(0)
            self.aggiungi_al_carrello()
        else:
            msg = createMessageBox(
                "Non trovato",
                f"Codice {codice} non trovato",
                QtWidgets.QMessageBox.Warning,
            )
            msg.exec_()

    def aggiungi_al_carrello(self):
        index = self.ui.tableStock.currentIndex()
        if not index.isValid():
            return

        row = index.row()
        barcode = self.model.data(self.model.index(row, self.model.fieldIndex("barcode")))
        espansione_id = self.model.data(self.model.index(row, self.model.fieldIndex("espansione_id")))
        espansione_nome = self.model.data(self.model.index(row, self.model.fieldIndex("espansione_nome")))
        nome = self.model.data(self.model.index(row, self.model.fieldIndex("name")))
        condizione = self.model.data(self.model.index(row, self.model.fieldIndex("condizione")))
        prezzo_stock = self.model.data(self.model.index(row, self.model.fieldIndex("prezzo")))
        quantita_stock = self.model.data(self.model.index(row, self.model.fieldIndex("quantita_stock")))
        stock_disponibile = int(quantita_stock)

        quantita_nel_carrello = 0

        for i in range(self.ui.tableWidget_carrello.rowCount()):
            if self.ui.tableWidget_carrello.item(i, 0).text() == str(barcode):
                quantita_nel_carrello += 1

        if quantita_nel_carrello >= stock_disponibile:
            msg = createMessageBox(
                title="Stock esaurito",
                text="La carta è attualmente non disponibile.",
                icon=QtWidgets.QMessageBox.Warning,
            )
            msg.exec_()
            return

        # aggiungi nuova riga
        row_pos = self.ui.tableWidget_carrello.rowCount()
        self.ui.tableWidget_carrello.insertRow(row_pos)
        barcode_item = QtWidgets.QTableWidgetItem(str(barcode))
        espansione_id_item = QtWidgets.QTableWidgetItem(str(espansione_id))
        espansione_nome_item = QtWidgets.QTableWidgetItem(str(espansione_nome))
        nome_item = QtWidgets.QTableWidgetItem(str(nome))
        condizione_item = QtWidgets.QTableWidgetItem(str(condizione))
        prezzo_item = QtWidgets.QTableWidgetItem(str(prezzo_stock))
        prezzo_vendita_item = QtWidgets.QTableWidgetItem(str(prezzo_stock))
        # ID NON editabile
        barcode_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Nome NON editabile
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo editabile
        # prezzo_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.ui.tableWidget_carrello.setItem(row_pos, 0, barcode_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 1, nome_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 2, espansione_id_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 3, espansione_nome_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 4, condizione_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 5, prezzo_item)
        self.ui.tableWidget_carrello.setItem(row_pos, 6, prezzo_vendita_item)

        # Pulsante rimuovi
        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon(":/icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)
        self.ui.tableWidget_carrello.setCellWidget(row_pos, 7, btn)

        self.aggiorna_totale()

    def rimuovi_dal_carrello(self):
        row = self.ui.tableWidget_carrello.currentRow()
        if row >= 0:
            self.ui.tableWidget_carrello.removeRow(row)

        self.aggiorna_totale()

    def rimuovi_riga_button(self):
        btn = self.sender()
        if not btn:
            return
        index_button = get_column_index(self.ui.tableWidget_carrello, " ")
        for row in range(self.ui.tableWidget_carrello.rowCount()):
            if self.ui.tableWidget_carrello.cellWidget(row, index_button) == btn:
                self.ui.tableWidget_carrello.removeRow(row)
                break

        self.aggiorna_totale()

    def svuota_carrello(self):
        self.ui.tableWidget_carrello.setRowCount(0)
        self.aggiorna_totale()

    def aggiorna_totale(self):
        totale = 0.0

        for row in range(self.ui.tableWidget_carrello.rowCount()):
            index_prezzo = get_column_index(self.ui.tableWidget_carrello, "Prezzo di vendita")
            item = self.ui.tableWidget_carrello.item(row, index_prezzo)  # colonna prezzo
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
            totale_scontato = float(testo.replace(",", "."))
        except ValueError:
            totale_scontato = 0.0
        if totale_scontato <= 0: return
        totale = float(self.ui.label_totale_carrello.text().replace(" €", ""))
        # sconto_per_riga = sconto / self.ui.tableWidget_carrello.rowCount()
        self.ui.label_totale_dapagare.setText(f"{totale_scontato:.2f} €")

        for row in range(self.ui.tableWidget_carrello.rowCount()):
            index_prezzo_stock = get_column_index(self.ui.tableWidget_carrello, "Prezzo stock")
            index_prezzo_scontato = get_column_index(self.ui.tableWidget_carrello, "Prezzo di vendita")
            prezzo_item = self.ui.tableWidget_carrello.item(row, index_prezzo_stock)
            prezzo_scontato_item = self.ui.tableWidget_carrello.item(row, index_prezzo_scontato)
            if prezzo_item is not None and prezzo_scontato_item is not None:
                try:
                    prezzo = float(prezzo_item.text())
                    if totale > 0:
                        prezzo_scontato = (
                            prezzo - (prezzo / totale) * (totale - totale_scontato)
                        )  # sconto proporzionale
                        # prezzo_scontato = prezzo - sconto_per_riga # sconto uniforme
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

    def concludi_vendita(self):
        if self.ui.tableWidget_carrello.rowCount() == 0:
            return

        # 🔒 inizio transazione
        self.db_main.transaction()

        try:
            for row in range(self.ui.tableWidget_carrello.rowCount()):
                barcode = self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "Barcode")).text()
                espansione_nome = self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "Nome Espansione")).text()
                espansione_id = self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "ID Espansione")).text()
                nome = self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "Nome")).text()
                condizione = self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "Condizione")).text()
                prezzo_stock = float(self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "Prezzo stock")).text())
                prezzo_vendita = float(self.ui.tableWidget_carrello.item(row, get_column_index(self.ui.tableWidget_carrello, "Prezzo di vendita")).text())
                sell_date = QtCore.QDateTime.currentDateTime().toString(
                    "yyyy-MM-dd HH:mm:ss"
                )

                # INSERT vendita
                insert_query = QtSql.QSqlQuery(self.db_main)
                insert_query.prepare("""
                    INSERT INTO sales (barcode, espansione_id, espansione_nome, nome, condizione, prezzo_stock, prezzo_vendita, sell_date)
                    VALUES (:barcode, :espansione_id, :espansione_nome, :nome, :condizione, :ps, :pv, :date)
                """)

                insert_query.bindValue(":barcode", barcode)
                insert_query.bindValue(":espansione_id", espansione_id)
                insert_query.bindValue(":espansione_nome", espansione_nome)
                insert_query.bindValue(":nome", nome)
                insert_query.bindValue(":condizione", condizione)
                insert_query.bindValue(":ps", prezzo_stock)
                insert_query.bindValue(":pv", prezzo_vendita)
                insert_query.bindValue(":date", sell_date)
                if not insert_query.exec_():
                    raise Exception(insert_query.lastError().text())

                # UPDATE stock
                update_query = QtSql.QSqlQuery(self.db_main)
                update_query.prepare(
                    "UPDATE stock SET quantita_stock = quantita_stock - 1 WHERE barcode = ?"
                )
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
                QtWidgets.QMessageBox.Critical,
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
