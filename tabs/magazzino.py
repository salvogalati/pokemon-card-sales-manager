from datetime import datetime
import os

from PyQt5 import QtWidgets
from PyQt5 import QtSql
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtCore import QSize

from utils import pulisci_testo, createMessageBox
from .models.magazzino_model import MagazzinoModel
from .models.delegates import YesNoDelegate, CondizioneComboBoxDelegate
from PyQt5.QtWidgets import QStyledItemDelegate, QSpinBox
from icons import icons  # noqa: F401
from config import main_db, backup_folder, cards_condizioni, get_resource_path, stock_table, unpriced_table
import shutil



class SpinBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setMinimum(0)
        editor.setMaximum(999999)
        return editor

    def setEditorData(self, editor, index):
        value = int(index.model().data(index))
        editor.setValue(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.value())


class MagazzinoTabController:
    def __init__(self, ui):
        self.ui = ui

        db = QtSql.QSqlDatabase.database("main_connection")
        self.model_magazzino = MagazzinoModel(db)
        self.model_magazzino.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model_magazzino.setTable(stock_table)
        self.model_magazzino.select()

        self.ui.tableViewMagazzino.setModel(self.model_magazzino)

        # self.ui.tableViewMagazzino.setItemDelegateForColumn(self.model_magazzino.fieldIndex("prezzo"), SpinBoxDelegate())
        delegateCondizione = CondizioneComboBoxDelegate(self.ui.tableViewMagazzino)
        self.ui.tableViewMagazzino.setItemDelegateForColumn(
            self.model_magazzino.fieldIndex("condizione"), delegateCondizione
        )
        self.ui.tableViewMagazzino.setIconSize(QSize(60, 60))
        self.ui.comboBoxCondizione.addItems(
            [""] + cards_condizioni
        )

        self.ui.button_applica_filtro.clicked.connect(self.applica_filtro)
        self.ui.button_resetta_filtro.clicked.connect(self.resetta_filtro)
        self.ui.buttonMagazzinoSave.clicked.connect(self.salva_modifiche)
        self.ui.buttonMagazzinoRipristina.clicked.connect(self.ripristina_backup)

        self.ui.lineEditSearchMagazzino.textChanged.connect(self.filtra_tabella_search)

        self.ui.buttonGroupMagazzino.buttonClicked.connect(self.on_magazzino_changed)

    def on_magazzino_changed(self, button):
        table_mapping = {"Prezzati": stock_table, "Da prezzare": unpriced_table}

        self.model_magazzino.setTable(table_mapping.get(button.text()))
        self.model_magazzino.select()

        delegateCondizione = CondizioneComboBoxDelegate(self.ui.tableViewMagazzino)
        self.ui.tableViewMagazzino.setItemDelegateForColumn(
            self.model_magazzino.fieldIndex("condizione"), delegateCondizione
        )
        if button.text() == "Da prezzare":
            delegateYesNo = YesNoDelegate(self.ui.tableViewMagazzino)
            self.ui.tableViewMagazzino.setItemDelegateForColumn(
                self.model_magazzino.fieldIndex("da_prezzare"), delegateYesNo
            )

        #self.applica_filtro()
        self.resetta_filtro()

    def applica_filtro(self):
        filtro_nome = self.ui.lineEditMagazzinoFiltroNome.text()
        filtro_espansione = self.ui.lineEditMagazzinoFiltroEspansione.text()
        filtro_qty = self.ui.spinBoxMagazzinoQty.value()
        filtro_condizione = self.ui.comboBoxCondizione.currentText()
        filtro_prezzo_min = self.ui.doubleSpinBoxMagazzinoPrezzoMin.value()
        filtro_prezzo_max = self.ui.doubleSpinBoxMagazzinoPrezzoMax.value()

        filtro_sql = self.check_filtri(
            filtro_nome,
            filtro_espansione,
            filtro_qty,
            filtro_condizione,
            filtro_prezzo_min,
            filtro_prezzo_max,
        )
        # ☻print(filtro_sql)
        self.model_magazzino.setFilter(filtro_sql)

    @staticmethod
    def check_filtri(
        filtro_nome,
        filtro_espansione,
        filtro_qty,
        filtro_condizione,
        filtro_prezzo_min,
        filtro_prezzo_max,
    ):
        def escape_sql(value):
            return value.replace("'", "''")

        condizioni = []

        if filtro_nome.strip():
            nome = escape_sql(filtro_nome)
            condizioni.append(f"name LIKE '%{nome}%'")

        if filtro_espansione.strip():
            esp = escape_sql(filtro_espansione)
            condizioni.append(f"espansione_id LIKE '%{esp}%' OR espansione_nome LIKE '%{esp}%'")

        if filtro_qty > 0:
            condizioni.append(f"quantita_stock >= {filtro_qty}")

        if filtro_condizione:
            cond = escape_sql(filtro_condizione)
            condizioni.append(f"condizione = '{cond}'")

        if filtro_prezzo_min > 0:
            condizioni.append(f"prezzo >= {filtro_prezzo_min}")

        if filtro_prezzo_max > 0:
            condizioni.append(f"prezzo <= {filtro_prezzo_max}")

        return " AND ".join(condizioni)

    def filtra_tabella_search(self, testo):
        if not testo:
            self.model_magazzino.setFilter("")
            self.model_magazzino.select()
            return
        testo_sicuro = pulisci_testo(testo)

        filtro = f"""
        espansione_id LIKE '%{testo_sicuro}%'
        OR espansione_nome LIKE '%{testo_sicuro}%'
        OR name LIKE '%{testo_sicuro}%'
        OR barcode LIKE '%{testo_sicuro}%'
        OR condizione LIKE '%{testo_sicuro}%'
        """

        self.model_magazzino.setFilter(filtro)
        self.model_magazzino.select()

    def resetta_filtro(self):
        self.ui.lineEditMagazzinoFiltroNome.clear()
        self.ui.lineEditMagazzinoFiltroEspansione.clear()
        self.ui.spinBoxMagazzinoQty.setValue(0)
        self.ui.comboBoxCondizione.setCurrentIndex(0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMin.setValue(0.0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMax.setValue(0.0)
        self.model_magazzino.setFilter("")

    def salva_modifiche(self):
        msg = createMessageBox(
            "Conferma Salvataggio",
            "Sei sicuro di voler salvare le modifiche al magazzino?",
            QtWidgets.QMessageBox.Question,
            [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No],
        )
        risposta = msg.exec_()
        if risposta == QMessageBox.No:
            return

        self.backup_database()
        if not self.model_magazzino.submitAll():
            QMessageBox.critical(
                self.ui,
                "Errore",
                f"Errore durante il salvataggio: {self.model_magazzino.lastError().text()}",
            )
        if self.model_magazzino.tableName() == unpriced_table:
            self.sposta_carte_prezzate()
        QMessageBox.information(
            self.ui, "Successo", "Modifiche salvate con successo!"
        )

    def sposta_carte_prezzate(self):
        db = QtSql.QSqlDatabase.database("main_connection")

        if not db.transaction():
            QMessageBox.critical(self.ui, "Errore", "Impossibile iniziare la transazione")
            return

        query = QtSql.QSqlQuery(db)

        try:
            chiave = "barcode" 

            # 1. UPDATE (merge su stock già esistente)
            update_sql = f"""
            UPDATE {stock_table}
            SET
                quantita_stock = quantita_stock + (
                    SELECT quantita_stock FROM {unpriced_table}
                    WHERE {unpriced_table}.{chiave} = {stock_table}.{chiave}
                    AND da_prezzare = 'No'
                ),

                prezzo = (
                    SELECT prezzo FROM {unpriced_table}
                    WHERE {unpriced_table}.{chiave} = {stock_table}.{chiave}
                    AND da_prezzare = 'No'
                ),

                prezzo_acquisto = ROUND(
                    (
                        (prezzo_acquisto * quantita_stock) +
                        (
                            (SELECT prezzo_acquisto FROM {unpriced_table}
                            WHERE {unpriced_table}.{chiave} = {stock_table}.{chiave}
                            AND da_prezzare = 'No')
                            *
                            (SELECT quantita_stock FROM {unpriced_table}
                            WHERE {unpriced_table}.{chiave} = {stock_table}.{chiave}
                            AND da_prezzare = 'No')
                        )
                    )
                    /
                    (
                        quantita_stock +
                        (SELECT quantita_stock FROM {unpriced_table}
                        WHERE {unpriced_table}.{chiave} = {stock_table}.{chiave}
                        AND da_prezzare = 'No')
                    ),
                2
                )

            WHERE EXISTS (
                SELECT 1 FROM {unpriced_table}
                WHERE {unpriced_table}.{chiave} = {stock_table}.{chiave}
                AND da_prezzare = 'No'
            )
            """

            if not query.exec_(update_sql):
                raise Exception(query.lastError().text())

            # 2. INSERT (solo nuove carte)
            insert_sql = f"""
            INSERT INTO {stock_table} (name, espansione_id, espansione_nome, quantita_stock, condizione, prezzo, prezzo_acquisto, barcode)
            SELECT name, espansione_id, espansione_nome, quantita_stock, condizione, prezzo, prezzo_acquisto, barcode
            FROM {unpriced_table} u
            WHERE da_prezzare = 'No'
            AND NOT EXISTS (
                SELECT 1 FROM {stock_table} s
                WHERE s.{chiave} = u.{chiave}
            )
            """

            if not query.exec_(insert_sql):
                raise Exception(query.lastError().text())

            # 3. DELETE da unpriced
            delete_sql = f"""
            DELETE FROM {unpriced_table}
            WHERE da_prezzare = 'No'
            """

            if not query.exec_(delete_sql):
                raise Exception(query.lastError().text())

            if not db.commit():
                raise Exception("Commit fallito")

            self.model_magazzino.select()

        except Exception as e:
            db.rollback()
            QMessageBox.critical(self.ui, "Errore", f"Errore nello spostamento:\n{str(e)}")

    def backup_database(self):
        try:
            date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_dir = get_resource_path(backup_folder)
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy(
                get_resource_path(main_db),
                os.path.join(
                    backup_dir,
                    f"backup_pokemon_cards_{date_now}.db",
                ),
            )
            # QMessageBox.information(self.ui, "Backup", "Backup del database creato con successo!")
        except Exception as e:
            QMessageBox.critical(
                self.ui,
                "Errore Backup",
                f"Errore durante il backup del databse\nAttenzione non sarà possibile ripristinare il database\nERRORE: {str(e)}",
            )

    def ripristina_backup(self):
        backup_dir = get_resource_path(backup_folder)
        backup_files = [
            f
            for f in os.listdir(backup_dir)
            if f.startswith("backup_pokemon_cards_") and f.endswith(".db")
        ]
        if not backup_files:
            QMessageBox.information(
                self.ui, "Nessun Backup", "Non sono stati trovati file di backup."
            )
            return
        backup_files.sort()
        backup_to_restore = backup_files[-1]  # Prendi l'ultimo backup creato
        data_backup = backup_to_restore.replace("backup_pokemon_cards_", "").replace(
            ".db", ""
        )
        msg = createMessageBox(
            "Conferma Ripristino",
            f"Sei sicuro di voler ripristinare il database dal backup più recente effettuato il {data_backup}?",
            QtWidgets.QMessageBox.Warning,
            [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No],
        )
        risposta = msg.exec_()

        if risposta == QMessageBox.No:
            return
        try:
            shutil.copy(
                os.path.join(backup_dir, backup_to_restore),
                get_resource_path(main_db),
            )
            self.model_magazzino.select()  # Ricarica i dati nel modello
            QMessageBox.information(
                self.ui, "Ripristino", "Database ripristinato con successo dal backup!"
            )
        except Exception as e:
            QMessageBox.critical(
                self.ui,
                "Errore Ripristino",
                f"Errore durante il ripristino del database\nERRORE: {str(e)}",
            )

