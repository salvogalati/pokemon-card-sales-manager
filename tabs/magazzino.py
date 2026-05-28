from datetime import datetime
import os
import traceback

from PyQt5 import QtWidgets
from PyQt5 import QtSql
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtCore import Qt

from utils import pulisci_testo, createMessageBox, auto_size_table_columns
from .models.magazzino_model import MagazzinoModel
from .models.delegates import (
    CenterIconDelegate,
    YesNoDelegate,
    CondizioneComboBoxDelegate,
)
from PyQt5.QtWidgets import QStyledItemDelegate, QSpinBox
from icons import icons  # noqa: F401
from config import (
    DBNames,
    FolderNames,
    FieldsEnum,
    get_resource_path,
    DBTables,
    card_condizioni_icons
)
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
        self.current_filter = ""  # Memorizza il filtro da applica_filtro

        db = QtSql.QSqlDatabase.database("main_connection")
        self.model_magazzino = MagazzinoModel(db)
        self.model_magazzino.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model_magazzino.setTable(DBTables.STOCK.value)
        self.model_magazzino.select()

        self.ui.tableViewMagazzino.setModel(self.model_magazzino)

        # self.ui.tableViewMagazzino.setItemDelegateForColumn(self.model_magazzino.fieldIndex("prezzo"), SpinBoxDelegate())
        delegateCondizione = CondizioneComboBoxDelegate(self.ui.tableViewMagazzino)
        self.ui.tableViewMagazzino.setItemDelegateForColumn(
            self.model_magazzino.fieldIndex(FieldsEnum.Condizione.value), delegateCondizione
        )
        for col in range(self.model_magazzino.columnCount()):
            field_name = self.model_magazzino.headerData(col, Qt.Horizontal)
            if field_name not in [e.value for e in FieldsEnum]:
                pass
                #elf.ui.tableViewMagazzino.hideColumn(col)
            else:
                field_name_ok = FieldsEnum(field_name).name.replace("_", " ")
                self.model_magazzino.setHeaderData(col, Qt.Horizontal, field_name_ok)

        self.ui.comboBoxCondizione.addItems([""] + list(card_condizioni_icons.keys()))

        self.ui.button_applica_filtro.clicked.connect(self.applica_filtro)
        self.ui.button_resetta_filtro.clicked.connect(self.resetta_filtro)
        self.ui.buttonMagazzinoSave.clicked.connect(self.salva_modifiche)
        self.ui.buttonMagazzinoRipristina.clicked.connect(self.ripristina_backup)

        self.ui.lineEditSearchMagazzino.textChanged.connect(self.filtra_tabella_search)

        self.ui.buttonGroupMagazzino.buttonClicked.connect(self.on_magazzino_changed)

        auto_size_table_columns(self.ui.tableViewMagazzino, padding=30)


    def on_magazzino_changed(self, button):
        table_mapping = {"Prezzati": DBTables.STOCK.value, "Da prezzare": DBTables.UNPRICED_CARDS.value}

        self.model_magazzino.setTable(table_mapping.get(button.text()))
        self.model_magazzino.select()

        delegateCondizione = CondizioneComboBoxDelegate(self.ui.tableViewMagazzino)
        self.ui.tableViewMagazzino.setItemDelegateForColumn(
            self.model_magazzino.fieldIndex(FieldsEnum.Condizione.value), delegateCondizione
        )

        if button.text() == "Da prezzare":
            delegateYesNo = YesNoDelegate(self.ui.tableViewMagazzino)
            self.ui.tableViewMagazzino.setItemDelegateForColumn(
                self.model_magazzino.fieldIndex(FieldsEnum.Da_Prezzare.value), delegateYesNo
            )

        for col in range(self.model_magazzino.columnCount()):
            field_name = self.model_magazzino.headerData(col, Qt.Horizontal)
            if field_name not in [e.value for e in FieldsEnum]:
                pass
                #elf.ui.tableViewMagazzino.hideColumn(col)
            else:
                field_name_ok = FieldsEnum(field_name).name.replace("_", " ")
                self.model_magazzino.setHeaderData(col, Qt.Horizontal, field_name_ok)

        # self.applica_filtro()
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
        # print(filtro_sql)
        self.model_magazzino.setFilter(filtro_sql)
        self.current_filter = filtro_sql

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
            condizioni.append(f"{FieldsEnum.Nome.value} LIKE '%{nome}%'")

        if filtro_espansione.strip():
            esp = escape_sql(filtro_espansione)
            condizioni.append(
                f"{FieldsEnum.Espansione_ID.value} LIKE '%{esp}%' OR '{FieldsEnum.Espansione.value}' LIKE '%{esp}%'"
            )

        if filtro_qty > 0:
            condizioni.append(f"{FieldsEnum.Quantità.value} >= {filtro_qty}")

        if filtro_condizione:
            cond = escape_sql(filtro_condizione)
            condizioni.append(f"{FieldsEnum.Condizione.value} = '{cond}'")

        if filtro_prezzo_min > 0:
            condizioni.append(f"{FieldsEnum.Prezzo.value} >= {filtro_prezzo_min}")

        if filtro_prezzo_max > 0:
            condizioni.append(f"{FieldsEnum.Prezzo.value} <= {filtro_prezzo_max}")

        return " AND ".join(condizioni)

    def filtra_tabella_search(self, testo):
        if not testo:
            self.model_magazzino.setFilter("")
            self.model_magazzino.select()
            return
        testo_sicuro = pulisci_testo(testo)

        filtro_ricerca = f"""
        {FieldsEnum.Espansione_ID.value} LIKE '%{testo_sicuro}%'
        OR '{FieldsEnum.Espansione.value}' LIKE '%{testo_sicuro}%'
        OR {FieldsEnum.Nome.value} LIKE '%{testo_sicuro}%'
        OR {FieldsEnum.Barcode.value} LIKE '%{testo_sicuro}%'
        OR {FieldsEnum.Condizione.value} LIKE '%{testo_sicuro}%'
        """
        if self.current_filter:
                filtro_combinato = f"({self.current_filter}) AND ({filtro_ricerca})"
        else:
            filtro_combinato = filtro_ricerca
        self.model_magazzino.setFilter(filtro_combinato)
        self.model_magazzino.select()

    def resetta_filtro(self):
        self.ui.lineEditMagazzinoFiltroNome.clear()
        self.ui.lineEditMagazzinoFiltroEspansione.clear()
        self.ui.spinBoxMagazzinoQty.setValue(0)
        self.ui.comboBoxCondizione.setCurrentIndex(0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMin.setValue(0.0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMax.setValue(0.0)
        self.model_magazzino.setFilter("")
        self.current_filter = ""

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
        self.ui.tableViewMagazzino.closeEditor(
            self.ui.tableViewMagazzino.focusWidget(),
            QtWidgets.QAbstractItemDelegate.NoHint
        )

        self.ui.tableViewMagazzino.clearFocus()
        ok = self.model_magazzino.submitAll()
        if not ok:
            QMessageBox.critical(
                self.ui,
                "Errore",
                f"Errore durante il salvataggio: {self.model_magazzino.lastError().text()}",
            )
            return
        if self.model_magazzino.tableName() == DBTables.UNPRICED_CARDS.value:
            self.sposta_carte_prezzate()
        QMessageBox.information(self.ui, "Successo", "Modifiche salvate con successo!")

    def sposta_carte_prezzate(self):
        db = QtSql.QSqlDatabase.database("main_connection")

        if not db.transaction():
            QMessageBox.critical(
                self.ui, "Errore", "Impossibile iniziare la transazione"
            )
            return

        query = QtSql.QSqlQuery(db)

        try:
            chiave = F"{FieldsEnum.Barcode.value}"  # Puoi modificare questa chiave se necessario

            # 1. UPDATE (merge su stock già esistente)
            update_sql = f"""
            UPDATE {DBTables.STOCK.value}
            SET
                {FieldsEnum.Quantità.value} = {FieldsEnum.Quantità.value} + (
                    SELECT {FieldsEnum.Quantità.value} FROM {DBTables.UNPRICED_CARDS.value}
                    WHERE {DBTables.UNPRICED_CARDS.value}.{chiave} = {DBTables.STOCK.value}.{chiave}
                    AND {FieldsEnum.Da_Prezzare.value} = 'No'
                ),

                {FieldsEnum.Prezzo.value} = (
                    SELECT {FieldsEnum.Prezzo.value} FROM {DBTables.UNPRICED_CARDS.value}
                    WHERE {DBTables.UNPRICED_CARDS.value}.{chiave} = {DBTables.STOCK.value}.{chiave}
                    AND {FieldsEnum.Da_Prezzare.value} = 'No'
                ),

                {FieldsEnum.Prezzo_Acquisto.value} = ROUND(
                    (
                        ({FieldsEnum.Prezzo_Acquisto.value} * {FieldsEnum.Quantità.value}) +
                        (
                            (SELECT {FieldsEnum.Prezzo.value} FROM {DBTables.UNPRICED_CARDS.value}
                            WHERE {DBTables.UNPRICED_CARDS.value}.{chiave} = {DBTables.STOCK.value}.{chiave}
                            AND {FieldsEnum.Da_Prezzare.value} = 'No')
                            *
                            (SELECT {FieldsEnum.Quantità.value} FROM {DBTables.UNPRICED_CARDS.value}
                            WHERE {DBTables.UNPRICED_CARDS.value}.{chiave} = {DBTables.STOCK.value}.{chiave}
                            AND {FieldsEnum.Da_Prezzare.value} = 'No')
                        )
                    )
                    /
                    (
                        {FieldsEnum.Quantità.value} +
                        (SELECT {FieldsEnum.Quantità.value} FROM {DBTables.UNPRICED_CARDS.value}
                        WHERE {DBTables.UNPRICED_CARDS.value}.{chiave} = {DBTables.STOCK.value}.{chiave}
                        AND {FieldsEnum.Da_Prezzare.value} = 'No')
                    ),
                2
                )

            WHERE EXISTS (
                SELECT 1 FROM {DBTables.UNPRICED_CARDS.value}
                WHERE {DBTables.UNPRICED_CARDS.value}.{chiave} = {DBTables.STOCK.value}.{chiave}
                AND {FieldsEnum.Da_Prezzare.value} = 'No'
            )
            """

            if not query.exec_(update_sql):
                raise Exception(query.lastError().text())

            # 2. INSERT (solo nuove carte)
            insert_sql = f"""
            INSERT INTO {DBTables.STOCK.value} ({FieldsEnum.Nome.value}, {FieldsEnum.ID_Cardmarket.value}, {FieldsEnum.Espansione_ID.value}, {FieldsEnum.Prezzo_Acquisto.value}, {FieldsEnum.Quantità.value}, {FieldsEnum.Condizione.value}, {FieldsEnum.Prezzo.value}, {FieldsEnum.Prezzo_Acquisto.value}, {FieldsEnum.Barcode.value})
            SELECT {FieldsEnum.Nome.value}, {FieldsEnum.ID_Carta.value}, {FieldsEnum.Espansione_ID.value}, {FieldsEnum.Prezzo_Acquisto.value}, {FieldsEnum.Quantità.value}, {FieldsEnum.Condizione.value}, {FieldsEnum.Prezzo.value}, {FieldsEnum.Prezzo_Acquisto.value}, {FieldsEnum.Barcode.value}
            FROM {DBTables.UNPRICED_CARDS.value} u
            WHERE {FieldsEnum.Da_Prezzare.value} = 'No'
            AND NOT EXISTS (
                SELECT 1 FROM {DBTables.STOCK.value} s
                WHERE s.{chiave} = u.{chiave}
            )
            """

            if not query.exec_(insert_sql):
                raise Exception(query.lastError().text())

            # 3. DELETE da unpriced
            delete_sql = f"""
            DELETE FROM {DBTables.UNPRICED_CARDS.value}
            WHERE {FieldsEnum.Da_Prezzare.value} = 'No'
            """

            if not query.exec_(delete_sql):
                raise Exception(query.lastError().text())

            if not db.commit():
                raise Exception("Commit fallito")

            self.model_magazzino.select()

        except Exception as e:
            db.rollback()
            QMessageBox.critical(
                self.ui, "Errore", f"Errore nello spostamento:\n{str(e)}"
            )
            print(traceback.format_exc())

    def backup_database(self):
        try:
            date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_dir = get_resource_path(FolderNames.BACKUPS.value)
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy(
                get_resource_path(DBNames.MAIN_DB.value),
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
        backup_dir = get_resource_path(FolderNames.BACKUPS.value)
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
                get_resource_path(DBNames.MAIN_DB.value),
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
