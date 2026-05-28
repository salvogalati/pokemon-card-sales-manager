import json

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt

from .models.card_database_model import CardDatabaseModel
from .models.delegates import CondizioneComboBoxDelegate1
from dialogs.apri_bozza_acquisti import ApriBozzaAcquistiDialog
from dialogs.salva_bozza_acquisti import SalvaBozzaAcquistiDialog
from utils import createMessageBox, get_column_index, generate_barcode, auto_size_table_columns
from config import DBTables, DBNames, FieldsEnum
from icons import icons  # noqa: F401

import traceback


class AcquistiTabController(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.bozza = None

        db_cards = QtSql.QSqlDatabase.database("card_db_connection")
        db_main = QtSql.QSqlDatabase.database("main_connection")
        self.db_main = db_main  # Assign the main database connection to self.db_main
        self.db = db_cards  # Assign the database connection to self.db
        self.model_card_database = CardDatabaseModel(db_cards)
        self.model_card_database.setTable(DBTables.DATABASE_CARDS.value)
        self.model_card_database.select()
        self.ui.tableDatabaseAcquisti.setModel(self.model_card_database)
        self.ui.tableDatabaseAcquisti.doubleClicked.connect(
            self.aggiungi_a_lista_acquisti
        )

        for col in range(self.model_card_database.columnCount()):

            field_name = self.model_card_database.headerData(col, Qt.Horizontal)  
            if field_name not in {FieldsEnum.ID_Cardmarket.value, FieldsEnum.Nome.value, FieldsEnum.Espansione.value, FieldsEnum.Espansione_ID.value}:
                self.ui.tableDatabaseAcquisti.hideColumn(col)
            else:
                field_name_ok = FieldsEnum(field_name).name.replace("_", " ")
                self.model_card_database.setHeaderData(col, Qt.Horizontal, field_name_ok)

        self.ui.lineEditCercaAcquisti.textChanged.connect(self.filtra_tabella)

        self.ui.tableWidgetAcquisti.setColumnCount(8)
        self.ui.tableWidgetAcquisti.setHorizontalHeaderLabels(
            [
                "ID Cardmarket",
                "ID Espansione",
                "Nome Espansione",
                "Nome",
                "Condizione",
                "Prezzo valutazione",
                "Prezzo acquisto",
                "",
            ]
        )
        delegateCondizione = CondizioneComboBoxDelegate1(self.ui.tableWidgetAcquisti)
        self.ui.tableWidgetAcquisti.setItemDelegateForColumn(4, delegateCondizione)

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

        auto_size_table_columns(self.ui.tableDatabaseAcquisti, padding=30)
        auto_size_table_columns(self.ui.tableWidgetAcquisti, padding=20)

    def filtra_tabella(self, testo):
        if not testo:
            self.model_card_database.setFilter("")
        else:
            filtro = f"""{FieldsEnum.Nome.value} LIKE '%{testo}%'
            OR {FieldsEnum.ID_Cardmarket.value} LIKE '%{testo}%'
            OR '{FieldsEnum.Espansione.value}' LIKE '%{testo}%'
            OR {FieldsEnum.Espansione_ID.value} LIKE '%{testo}%'"""
            self.model_card_database.setFilter(filtro)

    def aggiungi_a_lista_acquisti(self, index):
        if not index.isValid():
            return
        record = self.model_card_database.record(index.row())
        id_card = record.value(FieldsEnum.ID_Cardmarket.value)
        nome = record.value(FieldsEnum.Nome.value)
        espansione_id = record.value(FieldsEnum.Espansione_ID.value)
        espansione_nome = record.value(FieldsEnum.Espansione.value)

        row_pos = self.ui.tableWidgetAcquisti.rowCount()
        self.ui.tableWidgetAcquisti.insertRow(row_pos)
        id_item = QtWidgets.QTableWidgetItem(str(id_card))
        espansione_id_item = QtWidgets.QTableWidgetItem(str(espansione_id))
        espansione_nome_item = QtWidgets.QTableWidgetItem(str(espansione_nome))
        nome_item = QtWidgets.QTableWidgetItem(str(nome))
        condizione_item = QtWidgets.QTableWidgetItem("NM")
        prezzo_item_stima = QtWidgets.QTableWidgetItem(str(0))
        prezzo_item_acquisto = QtWidgets.QTableWidgetItem(str(0))


        # Solo prezzo_item_acquisto editabile, tutti gli altri non editabili
        id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        espansione_id_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        espansione_nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo acquisto editabile
        # prezzo_item_acquisto.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.ui.tableWidgetAcquisti.setItem(row_pos, 0, id_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 1, espansione_id_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 2, espansione_nome_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 3, nome_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 4, condizione_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 5, prezzo_item_stima)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 6, prezzo_item_acquisto)

        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon(":/icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)

        self.ui.tableWidgetAcquisti.setCellWidget(row_pos, 7, btn)
        self.aggiorna_totale()

    def aggiorna_totale(self, totale_da_pagare=None):
        totale = 0.0
        index_prezzo = get_column_index(
            self.ui.tableWidgetAcquisti, "Prezzo valutazione"
        )
        for row in range(self.ui.tableWidgetAcquisti.rowCount()):
            prezzo_item = self.ui.tableWidgetAcquisti.item(row, index_prezzo)
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
            pass
            # self.ui.lineEditTotaleDaPagareAcquisti.setText(f"{totale:.2f}")

        if self.ui.tableWidgetAcquisti.rowCount() > 0:
            self.ui.buttonSvuotaAcquisti.setEnabled(True)
            self.ui.buttonCompletaAcquisti.setEnabled(True)
            self.ui.buttonSalvaBozzaAcquisti.setEnabled(True)
        else:
            self.ui.buttonSvuotaAcquisti.setEnabled(False)
            self.ui.buttonCompletaAcquisti.setEnabled(False)
            self.ui.buttonSalvaBozzaAcquisti.setEnabled(False)

    def valida_prezzo(self, item):
        index_prezzo = get_column_index(
            self.ui.tableWidgetAcquisti, "Prezzo valutazione"
        )
        index_acquisto = get_column_index(
            self.ui.tableWidgetAcquisti, "Prezzo acquisto"
        )
        if item.column() in [index_prezzo, index_acquisto]:  # Colonna del prezzo
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
        except ValueError:
            print("Totale da pagare non valido. Deve essere un numero.")
            return
        self.ui.tableWidgetAcquisti.blockSignals(True)
        index_prezzo = get_column_index(
            self.ui.tableWidgetAcquisti, "Prezzo valutazione"
        )
        index_acquisto = get_column_index(
            self.ui.tableWidgetAcquisti, "Prezzo acquisto"
        )

        for row in range(self.ui.tableWidgetAcquisti.rowCount()):
            prezzo_item = self.ui.tableWidgetAcquisti.item(row, index_prezzo)
            prezzo_acquisto_item = self.ui.tableWidgetAcquisti.item(row, index_acquisto)
            try:
                if prezzo_item and prezzo_acquisto_item:
                    prezzo_stima = float(prezzo_item.text())
                    prezzo_acquisto = prezzo_stima * (
                        totale_da_pagare
                        / float(self.ui.labelTotaleAcquisti.text().replace("€", ""))
                    )
                    prezzo_acquisto_item.setText(f"{prezzo_acquisto:.2f}")
            except ValueError:
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
        self.ui.lineEditTotaleDaPagareAcquisti.setText("")
        self.bozza = None
        self.aggiorna_totale()

    def completa_acquisti(self):
        if self.ui.tableWidgetAcquisti.rowCount() == 0:
            return

        self.db_main.transaction()

        try:
            for row in range(self.ui.tableWidgetAcquisti.rowCount()):
                row_data = {}
                for col in range(self.ui.tableWidgetAcquisti.columnCount()):
                    item = self.ui.tableWidgetAcquisti.item(row, col)
                    if item:
                        header = self.ui.tableWidgetAcquisti.horizontalHeaderItem(
                            col
                        ).text()
                        row_data[header] = item.text()
                barcode = generate_barcode(
                    row_data["Nome"], row_data["ID Espansione"], row_data["Condizione"]
                )
                acquisto_date = QtCore.QDateTime.currentDateTime().toString(
                    "yyyy-MM-dd HH:mm:ss"
                )

                insert_query = QtSql.QSqlQuery(self.db_main)
                insert_query.prepare(f"""
                    INSERT INTO {DBTables.PURCHASES.value} ({FieldsEnum.Barcode.value}, {FieldsEnum.Espansione_ID.value}, '{FieldsEnum.Espansione.value}', {FieldsEnum.Nome.value}, {FieldsEnum.Condizione.value}, {FieldsEnum.Prezzo.value}, {FieldsEnum.Data_Acquisto.value})
                    VALUES (:barcode, :espansione_id, :espansione_nome, :nome, :condizione, :prezzo, :data)
                """)
                insert_query.bindValue(":barcode", barcode)
                insert_query.bindValue(":espansione_id", row_data["ID Espansione"])
                insert_query.bindValue(":espansione_nome", row_data["Nome Espansione"])
                insert_query.bindValue(":nome", row_data["Nome"])
                insert_query.bindValue(":condizione", row_data["Condizione"])
                insert_query.bindValue(":prezzo", row_data["Prezzo acquisto"])
                insert_query.bindValue(":data", acquisto_date)
                if not insert_query.exec_():
                    print("SQL ERROR:", insert_query.lastError().text())
                    print("QUERY:", insert_query.lastQuery())
                    print("BOUND:", insert_query.boundValues())
                    raise Exception(insert_query.lastError().text())

                # Logica per aggiornare lo stock: se la carta esiste già
                # update_query = QtSql.QSqlQuery(self.db_main)
                # update_query.prepare(f"""
                #     UPDATE {stock_table}
                #     SET quantita_stock = quantita_stock + 1
                #     WHERE barcode = :barcode
                # """)
                # update_query.bindValue(":prezzo", row_data["Prezzo acquisto"])
                # update_query.bindValue(":barcode", barcode)
                # if not update_query.exec_():
                #     raise Exception(update_query.lastError().text())

                # if update_query.numRowsAffected() == 0:

                insert_stock_query = QtSql.QSqlQuery(self.db_main)
                insert_stock_query.prepare(f"""
                    INSERT INTO {DBTables.UNPRICED_CARDS.value} ({FieldsEnum.Barcode.value}, {FieldsEnum.ID_Carta.value}, {FieldsEnum.Espansione_ID.value}, '{FieldsEnum.Espansione.value}', {FieldsEnum.Nome.value}, {FieldsEnum.Condizione.value}, {FieldsEnum.Prezzo.value}, {FieldsEnum.Quantità.value}, {FieldsEnum.Prezzo_Acquisto.value}, {FieldsEnum.Da_Prezzare.value})
                    VALUES (:barcode, :id, :espansione_id, :espansione_nome, :name, :condizione, :prezzo, 1, :prezzo_acquisto, 'Si')
                """)
                insert_stock_query.bindValue(":barcode", barcode)
                insert_stock_query.bindValue(":id", row_data["ID Cardmarket"])
                insert_stock_query.bindValue(
                    ":espansione_id", row_data["ID Espansione"]
                )
                insert_stock_query.bindValue(
                    ":espansione_nome", row_data["Nome Espansione"]
                )
                insert_stock_query.bindValue(":name", row_data["Nome"])
                insert_stock_query.bindValue(":condizione", row_data["Condizione"])
                insert_stock_query.bindValue(
                    ":prezzo", float(row_data["Prezzo acquisto"])
                )
                insert_stock_query.bindValue(
                    ":prezzo_acquisto", float(row_data["Prezzo acquisto"])
                )
                if not insert_stock_query.exec_():
                    raise Exception(insert_stock_query.lastError().text())

            self.db_main.commit()
            self.ui.lineEditTotaleDaPagareAcquisti.setText("")
            self.bozza = None

        except Exception as e:
            self.db_main.rollback()
            msg = createMessageBox(
                "Errore",
                f"Errore durante l'acquisto:\n{str(e)}",
                QtWidgets.QMessageBox.Critical,
            )
            msg.exec_()

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
            data.append(
                {
                    FieldsEnum.ID_Cardmarket.value: self.ui.tableWidgetAcquisti.item(
                        row, get_column_index(self.ui.tableWidgetAcquisti, "ID Cardmarket")
                    ).text(),
                    FieldsEnum.Espansione_ID.value: self.ui.tableWidgetAcquisti.item(
                        row,
                        get_column_index(self.ui.tableWidgetAcquisti, "ID Espansione"),
                    ).text(),
                    FieldsEnum.Espansione.value: self.ui.tableWidgetAcquisti.item(
                        row,
                        get_column_index(
                            self.ui.tableWidgetAcquisti, "Nome Espansione"
                        ),
                    ).text(),
                    FieldsEnum.Nome.value: self.ui.tableWidgetAcquisti.item(
                        row, get_column_index(self.ui.tableWidgetAcquisti, "Nome")
                    ).text(),
                    FieldsEnum.Condizione.value: self.ui.tableWidgetAcquisti.item(
                        row, get_column_index(self.ui.tableWidgetAcquisti, "Condizione")
                    ).text(),
                    FieldsEnum.Prezzo_Valutazione.value: self.ui.tableWidgetAcquisti.item(
                        row,
                        get_column_index(
                            self.ui.tableWidgetAcquisti, "Prezzo valutazione"
                        ),
                    ).text(),
                    FieldsEnum.Prezzo_Acquisto.value: self.ui.tableWidgetAcquisti.item(
                        row,
                        get_column_index(
                            self.ui.tableWidgetAcquisti, "Prezzo acquisto"
                        ),
                    ).text(),
                }
            )

        data_json = json.dumps(data)
        dialog = SalvaBozzaAcquistiDialog(data_json, parent=self)
        if self.bozza:
            msg = createMessageBox(
                "Bozza esistente", f"Stai modificando una bozza esistente. Vuoi sovrascrivere la bozza {self.bozza}?",
                QtWidgets.QMessageBox.Warning, buttons=[QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No])
            if msg.exec_() == QtWidgets.QMessageBox.Yes:
                dialog.update_bozza(data=data_json,name=self.bozza)
            else:
                dialog.exec_()
        else:
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
                print(traceback.format_exc())
                return
            self.svuota_lista_acquisti()
            self.ui.tableWidgetAcquisti.blockSignals(True)
            for item in data:
                print(item)
                row_pos = self.ui.tableWidgetAcquisti.rowCount()
                self.ui.tableWidgetAcquisti.insertRow(row_pos)
                id_item = QtWidgets.QTableWidgetItem(str(item.get(FieldsEnum.ID_Cardmarket.value, "")))
                espansione_id_item = QtWidgets.QTableWidgetItem(
                    str(item.get(FieldsEnum.Espansione_ID.value, ""))
                )
                espansione_nome_item = QtWidgets.QTableWidgetItem(
                    str(item.get(FieldsEnum.Espansione.value, ""))
                )
                nome_item = QtWidgets.QTableWidgetItem(str(item.get(FieldsEnum.Nome.value, "")))
                condizione_item = QtWidgets.QTableWidgetItem(
                    str(item.get(FieldsEnum.Condizione.value, "Mint"))
                )
                prezzo_item_valutazione = QtWidgets.QTableWidgetItem(
                    str(item.get(FieldsEnum.Prezzo_Valutazione.value, "0"))
                )
                prezzo_item_acquisto = QtWidgets.QTableWidgetItem(
                    str(item.get(FieldsEnum.Prezzo_Acquisto.value, "0"))
                )

                nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                prezzo_item_acquisto.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                prezzo_item_valutazione.setFlags(
                    Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                )

                self.ui.tableWidgetAcquisti.setItem(row_pos, 0, id_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 1, espansione_id_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 2, espansione_nome_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 3, nome_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 4, condizione_item)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 5, prezzo_item_valutazione)
                self.ui.tableWidgetAcquisti.setItem(row_pos, 6, prezzo_item_acquisto)

                btn = QtWidgets.QPushButton("")
                btn.setIcon(QtGui.QIcon(":/icons/trash-2.svg"))
                btn.setToolTip("Rimuovi dal carrello")
                btn.clicked.connect(self.rimuovi_riga_button)

                self.ui.tableWidgetAcquisti.setCellWidget(row_pos, 7, btn)
            self.ui.tableWidgetAcquisti.blockSignals(True)
            self.aggiorna_totale(totale_da_pagare=float(dialog.totale))
            self.bozza = dialog.nome_bozza
