from datetime import datetime
import json

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt

from .models.card_database_model import CardDatabaseModel
from .models.delegates import CondizioneComboBoxDelegate
from dialogs.apri_bozza_acquisti import ApriBozzaAcquistiDialog
from dialogs.salva_bozza_acquisti import SalvaBozzaAcquistiDialog   
from utils import createMessageBox

from icons import icons  # noqa: F401


class AcquistiTabController(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

        db_cards = QtSql.QSqlDatabase.database("card_db_connection")
        db_main = QtSql.QSqlDatabase.database("main_connection")
        self.db_main = db_main  # Assign the main database connection to self.db_main
        self.db = db_cards  # Assign the database connection to self.db
        self.model_card_database = CardDatabaseModel(db_cards)
        self.model_card_database.setTable("stock")
        self.model_card_database.select()
        self.ui.tableDatabaseAcquisti.setModel(self.model_card_database)
        self.ui.tableDatabaseAcquisti.doubleClicked.connect(
            self.aggiungi_a_lista_acquisti
        )


        self.ui.lineEditCercaAcquisti.textChanged.connect(self.filtra_tabella)

        self.ui.tableWidgetAcquisti.setColumnCount(6)
        self.ui.tableWidgetAcquisti.setHorizontalHeaderLabels(
            ["Espansione", "Nome", "Condizione", "Prezzo valutazione", "Prezzo acquisto", ""]
        )
        delegateCondizione = CondizioneComboBoxDelegate(self.ui.tableWidgetAcquisti)
        self.ui.tableWidgetAcquisti.setItemDelegateForColumn(
           2, delegateCondizione
        )

        self.ui.tableWidgetAcquisti.itemChanged.connect(self.valida_prezzo)

        self.ui.buttonSvuotaAcquisti.clicked.connect(self.svuota_lista_acquisti)

        self.ui.buttonCompletaAcquisti.clicked.connect(self.completa_acquisti)

        # Timer per aggiornamento ritardato del prezzo totale
        self.timer_ricalcolo = QtCore.QTimer()
        self.timer_ricalcolo.setSingleShot(True)
        self.timer_ricalcolo.timeout.connect(self.aggiorna_prezzo_totale)
        self.ui.lineEditTotaleDaPagareAcquisti.textChanged.connect(self.delayed_update)

        self.ui.buttonSalvaBozzaAcquisti.clicked.connect(self.salva_bozza_acquisti)
        self.ui.buttonApriBozzaAcquisti.clicked.connect(self.apri_bozza_acquisti)

    def filtra_tabella(self, testo):
        if not testo:
            self.model_card_database.setFilter("")
        else:
            filtro = f"nome LIKE '%{testo}%' OR espansione LIKE '%{testo}%'"
            self.model_card_database.setFilter(filtro)

    def aggiungi_a_lista_acquisti(self, index):
        if not index.isValid():
            return
        record = self.model_card_database.record(index.row())
        nome = record.value("nome")
        espansione = record.value("espansione")

        row_pos = self.ui.tableWidgetAcquisti.rowCount()
        self.ui.tableWidgetAcquisti.insertRow(row_pos)
        espansione_item = QtWidgets.QTableWidgetItem(str(espansione))
        nome_item = QtWidgets.QTableWidgetItem(str(nome))
        condizione_item = QtWidgets.QTableWidgetItem("Mint")
        prezzo_item_stima = QtWidgets.QTableWidgetItem(str(0))
        prezzo_item_acquisto = QtWidgets.QTableWidgetItem(str(0))


        # Nome NON editabile
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        prezzo_item_acquisto.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo editabile
        prezzo_item_stima.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.ui.tableWidgetAcquisti.setItem(row_pos, 0, espansione_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 1, nome_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 2, condizione_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 3, prezzo_item_stima)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 4, prezzo_item_acquisto)

        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon(":/icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)

        self.ui.tableWidgetAcquisti.setCellWidget(row_pos, 5, btn)
        self.aggiorna_totale()

    def aggiorna_totale(self, totale_da_pagare=None):
        totale = 0.0
        for row in range(self.ui.tableWidgetAcquisti.rowCount()):
            prezzo_item = self.ui.tableWidgetAcquisti.item(row, 3)
            if prezzo_item:
                try:
                    prezzo = float(prezzo_item.text())
                    totale += prezzo
                except ValueError:
                    pass  # Ignora valori non numerici
        self.ui.labelTotaleAcquisti.setText(f"€{totale:.2f}")
        if totale_da_pagare is not None:
            self.ui.lineEditTotaleDaPagareAcquisti.setText(f"{totale_da_pagare:.2f}")
        else:
            self.ui.lineEditTotaleDaPagareAcquisti.setText(f"{totale:.2f}")

        if self.ui.tableWidgetAcquisti.rowCount() > 0:
            self.ui.buttonSvuotaAcquisti.setEnabled(True)
            self.ui.buttonCompletaAcquisti.setEnabled(True)
            self.ui.buttonSalvaBozzaAcquisti.setEnabled(True)
        else:
            self.ui.buttonSvuotaAcquisti.setEnabled(False)
            self.ui.buttonCompletaAcquisti.setEnabled(False)
            self.ui.buttonSalvaBozzaAcquisti.setEnabled(False)

    def valida_prezzo(self, item):
        if item.column() in [3, 4]:  # Colonna del prezzo
            try:
                prezzo = float(item.text())
                if prezzo < 0:
                    print("Prezzo non valido. Deve essere un numero positivo.")
            except ValueError:
                print("Prezzo non valido. Deve essere un numero positivo.")
                # item.setText("0")  # Reset al valore precedente o a zero
            self.aggiorna_totale()

    def delayed_update(self):
        self.timer_ricalcolo.start(300)

    def aggiorna_prezzo_totale(self):
        try:
            totale_da_pagare = float(self.ui.lineEditTotaleDaPagareAcquisti.text())
        except:
            print("Totale da pagare non valido. Deve essere un numero.")
            return
        self.ui.tableWidgetAcquisti.blockSignals(True)

        for row in range(self.ui.tableWidgetAcquisti.rowCount()):
            prezzo_item = self.ui.tableWidgetAcquisti.item(row, 3)
            prezzo_acquisto_item = self.ui.tableWidgetAcquisti.item(row, 4)
            try:
                if prezzo_item and prezzo_acquisto_item:
                    prezzo_stima = float(prezzo_item.text())
                    prezzo_acquisto = prezzo_stima * (totale_da_pagare / float(self.ui.labelTotaleAcquisti.text().replace("€", "")))
                    prezzo_acquisto_item.setText(f"{prezzo_acquisto:.2f}")
            except:
                print("Errore nel calcolo del prezzo di acquisto.")
                continue
        self.ui.tableWidgetAcquisti.blockSignals(False)

    def rimuovi_riga_button(self):
        btn = self.sender()
        index = self.ui.tableWidgetAcquisti.indexAt(btn.pos())
        row = index.row()

        self.ui.tableWidgetAcquisti.removeRow(row)
        self.aggiorna_totale()

    def svuota_lista_acquisti(self):
        self.ui.tableWidgetAcquisti.setRowCount(0)
        self.aggiorna_totale()

    def completa_acquisti(self):
        if self.ui.tableWidgetAcquisti.rowCount() == 0:
            return

        self.db_main.transaction()

        try:
            for row in range(self.ui.tableWidgetAcquisti.rowCount()):
                espansione = self.ui.tableWidgetAcquisti.item(row, 0).text()
                nome = self.ui.tableWidgetAcquisti.item(row, 1).text()

                condizione = self.ui.tableWidgetAcquisti.item(row, 2).text()
                prezzo_acquisto = float(self.ui.tableWidgetAcquisti.item(row, 4).text())
                barcode = self.generate_barcode(nome, espansione, condizione)
                acquisto_date = QtCore.QDateTime.currentDateTime().toString(
                    "yyyy-MM-dd HH:mm:ss"
                )

                insert_query = QtSql.QSqlQuery(self.db_main)
                insert_query.prepare("""
                    INSERT INTO purchase (barcode,espansione, nome,condizione, prezzo_acquisto, purchase_date)
                    VALUES (:barcode, :espansione, :nome, :condizione, :prezzo, :data)
                """)
                insert_query.bindValue(":barcode", barcode)
                insert_query.bindValue(":espansione", espansione)
                insert_query.bindValue(":nome", nome)
                insert_query.bindValue(":condizione", condizione)
                insert_query.bindValue(":prezzo", prezzo_acquisto)
                insert_query.bindValue(":data", acquisto_date)
                if not insert_query.exec_():
                    raise Exception(insert_query.lastError().text())

                update_query = QtSql.QSqlQuery(self.db_main)
                update_query.prepare("""
                    UPDATE stock
                    SET quantita_stock = quantita_stock + 1,
                        prezzo = :prezzo
                    WHERE barcode = :barcode
                """)
                update_query.bindValue(":prezzo", prezzo_acquisto)
                update_query.bindValue(":barcode", barcode)
                if not update_query.exec_():
                    raise Exception(update_query.lastError().text())

                if update_query.numRowsAffected() == 0:
                    insert_stock_query = QtSql.QSqlQuery(self.db_main)
                    insert_stock_query.prepare("""
                        INSERT INTO stock (barcode, espansione, nome, condizione, prezzo, quantita_stock, prezzo_acquisto, da_prezzare)
                        VALUES (:barcode, :espansione, :nome, :condizione, :prezzo, 1, :prezzo_acquisto, 'Si')
                    """)
                    insert_stock_query.bindValue(":barcode", barcode)
                    insert_stock_query.bindValue(":espansione", espansione)
                    insert_stock_query.bindValue(":nome", nome)
                    insert_stock_query.bindValue(":condizione", condizione)
                    insert_stock_query.bindValue(":prezzo", float(prezzo_acquisto))
                    insert_stock_query.bindValue(
                        ":prezzo_acquisto", float(prezzo_acquisto)
                    )
                    if not insert_stock_query.exec_():
                        raise Exception(insert_stock_query.lastError().text())

            self.db_main.commit()

        except Exception as e:
            self.db_main.rollback()
            msg = createMessageBox(
                "Errore",
                f"Errore durante l'acquisto:\n{str(e)}",
                QtWidgets.QMessageBox.Critical,
            )
            msg.exec_()
            import traceback

            traceback.print_exc()
            return

        self.model_card_database.select()

        msg = createMessageBox(
            "Acquisto completato",
            "L'acquisto è stato registrato con successo!",
            QtWidgets.QMessageBox.Information,
        )
        msg.exec_()

        self.svuota_lista_acquisti()

    def salva_bozza_acquisti(self):
        if self.ui.tableWidgetAcquisti.rowCount() == 0:
            msg = createMessageBox("Errore", "La lista acquisti è vuota.")
            msg.exec_()
            return 
        data = []
        for row in range(self.ui.tableWidgetAcquisti.rowCount()):
            espansione = self.ui.tableWidgetAcquisti.item(row, 0).text()
            nome = self.ui.tableWidgetAcquisti.item(row, 1).text()
            condizione = self.ui.tableWidgetAcquisti.item(row, 2).text()
            prezzo_valutazione = self.ui.tableWidgetAcquisti.item(row, 3).text()
            prezzo_acquisto = self.ui.tableWidgetAcquisti.item(row, 4).text()
            data.append({
                "espansione": espansione,
                "nome": nome,
                "condizione": condizione,
                "prezzo_valutazione": prezzo_valutazione,
                "prezzo_acquisto": prezzo_acquisto
            })
        data_json = json.dumps(data)
        dialog = SalvaBozzaAcquistiDialog(data_json, parent=self)
        dialog.exec_()

    def apri_bozza_acquisti(self):
        dialog = ApriBozzaAcquistiDialog(None, parent=self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            data_json = dialog.data
            try:
                data = json.loads(data_json)
            except json.JSONDecodeError:
                msg = createMessageBox("Errore", "Dati della bozza non validi.")
                msg.exec_()
                return
            self.svuota_lista_acquisti()
            self.ui.tableWidgetAcquisti.blockSignals(True)
            for item in data:
                espansione = item.get("espansione", "")
                nome = item.get("nome", "")
                condizione = item.get("condizione", "Mint")
                prezzo_valutazione = item.get("prezzo_valutazione", "0")
                prezzo_acquisto = item.get("prezzo_acquisto", "0")

                row_pos = self.ui.tableWidgetAcquisti.rowCount()
                self.ui.tableWidgetAcquisti.insertRow(row_pos)
                espansione_item = QtWidgets.QTableWidgetItem(str(espansione))
                nome_item = QtWidgets.QTableWidgetItem(str(nome))
                condizione_item = QtWidgets.QTableWidgetItem(str(condizione))
                prezzo_item_valutazione = QtWidgets.QTableWidgetItem(str(prezzo_valutazione))
                prezzo_item_acquisto = QtWidgets.QTableWidgetItem(str(prezzo_acquisto))

                nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                prezzo_item_acquisto.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                prezzo_item_valutazione.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

                self.ui.tableWidgetAcquisti.setItem(row_pos, 0, espansione_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 1, nome_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 2, condizione_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 3, prezzo_item_valutazione)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 4, prezzo_item_acquisto)

                btn = QtWidgets.QPushButton("")
                btn.setIcon(QtGui.QIcon(":/icons/trash-2.svg"))
                btn.setToolTip("Rimuovi dal carrello")
                btn.clicked.connect(self.rimuovi_riga_button)

                self.ui.tableWidgetAcquisti.setCellWidget(row_pos, 5, btn)
            self.ui.tableWidgetAcquisti.blockSignals(True)
            self.aggiorna_totale(totale_da_pagare=float(dialog.totale))
                

    @staticmethod
    def generate_barcode(name, expansion, condition):
        # Semplice generatore di barcode basato su nome ed espansione
        base = f"{name}-{expansion}-{condition}"
        return base.upper()

