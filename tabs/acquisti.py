from datetime import datetime

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QTableView
from PyQt5.QtSql import QSqlQuery, QSqlTableModel, QSqlDatabase
from .models.card_database_model import CardDatabaseModel

from icons import icons_rc



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
        self.ui.tableDatabaseAcquisti.doubleClicked.connect(self.aggiungi_a_lista_acquisti)
    
        self.ui.lineEdit.textChanged.connect(self.filtra_tabella)

        self.ui.tableWidgetAcquisti.setColumnCount(5)
        self.ui.tableWidgetAcquisti.setHorizontalHeaderLabels(["Espansione", "Nome", "Condizione", "Prezzo stock", " "])

        self.ui.tableWidgetAcquisti.itemChanged.connect(self.valida_prezzo)

        self.ui.buttonSvuotaAcquisti.clicked.connect(self.svuota_lista_acquisti)

        self.ui.buttonCompletaAcquisti.clicked.connect(self.completa_acquisti)


    def filtra_tabella(self, testo):
        if not testo:
            self.model_card_database.setFilter("")
        else:
            filtro = f"name LIKE '%{testo}%' OR expansion LIKE '%{testo}%'"
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
        prezzo_item = QtWidgets.QTableWidgetItem(str(0))

        # Nome NON editabile
        nome_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

        # Prezzo editabile
        prezzo_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable)

        self.ui.tableWidgetAcquisti.setItem(row_pos, 0, espansione_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 1, nome_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 2, condizione_item)
        self.ui.tableWidgetAcquisti.setItem(row_pos, 3, prezzo_item)

        btn = QtWidgets.QPushButton("")
        btn.setIcon(QtGui.QIcon("icons/trash-2.svg"))
        btn.setToolTip("Rimuovi dal carrello")
        btn.clicked.connect(self.rimuovi_riga_button)

        self.ui.tableWidgetAcquisti.setCellWidget(row_pos, 4, btn)


        self.aggiorna_totale()

    def aggiorna_totale(self):
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

        if self.ui.tableWidgetAcquisti.rowCount() > 0:
            self.ui.buttonSvuotaAcquisti.setEnabled(True)
            self.ui.buttonCompletaAcquisti.setEnabled(True)
        else:     
            self.ui.buttonSvuotaAcquisti.setEnabled(False)
            self.ui.buttonCompletaAcquisti.setEnabled(False)

    def valida_prezzo(self, item):
        if item.column() == 3:  # Colonna del prezzo
            try:
                prezzo = float(item.text())
                if prezzo < 0:
                    print("Prezzo non valido. Deve essere un numero positivo.")
            except ValueError:
                print("Prezzo non valido. Deve essere un numero positivo.")
                #item.setText("0")  # Reset al valore precedente o a zero
            self.aggiorna_totale()

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
                prezzo_acquisto = float(self.ui.tableWidgetAcquisti.item(row, 3).text())
                barcode = self.generate_barcode(nome, espansione, condizione)
                acquisto_date = QtCore.QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

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
                        VALUES (:barcode, :espansione, :nome, :condizione, :prezzo, 1, :prezzo_acquisto, true)
                    """)
                    insert_stock_query.bindValue(":barcode", barcode)
                    insert_stock_query.bindValue(":espansione", espansione)
                    insert_stock_query.bindValue(":nome", nome)
                    insert_stock_query.bindValue(":condizione", condizione)
                    insert_stock_query.bindValue(":prezzo", float(prezzo_acquisto))
                    insert_stock_query.bindValue(":prezzo_acquisto", float(prezzo_acquisto))
                    if not insert_stock_query.exec_():
                        raise Exception(insert_stock_query.lastError().text())

            self.db_main.commit()

        except Exception as e:
            self.db_main.rollback()
            msg = self.createMessageBox(
                "Errore",
                f"Errore durante l'acquisto:\n{str(e)}",
                QtWidgets.QMessageBox.Critical
            )
            msg.exec_()
            import traceback
            traceback.print_exc()
            return

        self.model_card_database.select()

        msg = self.createMessageBox(
            "Acquisto completato",
            "L'acquisto è stato registrato con successo!",
            QtWidgets.QMessageBox.Information,
        )
        msg.exec_()

        self.svuota_lista_acquisti()

    @staticmethod
    def generate_barcode(name, expansion, condition):
        # Semplice generatore di barcode basato su nome ed espansione
        base = f"{name}-{expansion}-{condition}"
        return base.upper()

    def createMessageBox(self, title, text, icon=QtWidgets.QMessageBox.Information , buttons=[]):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setWindowIcon(QtGui.QIcon("icons/logo_kingdom_cards.png"))
        for button in buttons:
            msg.addButton(button)
        return msg