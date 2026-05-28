from PyQt5 import QtWidgets, uic, QtSql
from PyQt5 import QtCore
from config import DBTables, FieldsEnum, get_resource_path
from utils import createMessageBox
import os


class ApriBozzaAcquistiDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__()
        self.data = data

        # Carica il file .ui
        uic.loadUi(
            get_resource_path(os.path.join("ui", "dialog_bozze_acquisti.ui")), self
        )

        self.main_db = parent.db_main
        self.model = QtSql.QSqlTableModel(self, self.main_db)
        self.model.setTable(DBTables.BOZZE_ACQUISTI.value)
        self.model.setEditStrategy(QtSql.QSqlTableModel.OnManualSubmit)
        self.model.select()
        self.tableViewBozzeAcquisti.setModel(self.model)

        self.tableViewBozzeAcquisti.hideColumn(0)
        self.tableViewBozzeAcquisti.hideColumn(4)

        # Modifica nomi colonne visivamente (senza modificare il database)
        colonne = ["ID", "Nome Cliente", "Numero Oggetti", "Totale", "Oggetti"]
        for i, col_name in enumerate(colonne):
            self.model.setHeaderData(i, QtCore.Qt.Horizontal, col_name)

        self.lineEditSearchBozzeAcquisti.textChanged.connect(self.filter_bozze)
        self.buttonCancellaBozza.clicked.connect(self.cancella_bozza)
        self.buttonSvuotaBozze.clicked.connect(self.svuota_bozze)

    def accept(self):
        selected_indexes = self.tableViewBozzeAcquisti.selectionModel().selectedRows()
        if not selected_indexes:
            msg = createMessageBox("Errore", "Seleziona una bozza da aprire.")
            msg.exec_()
            return
        selected_row = selected_indexes[0].row()
        oggetti_data = self.model.record(selected_row).value(f"{FieldsEnum.Oggetti.value}")
        nome_bozza = self.model.record(selected_row).value(f"{FieldsEnum.Nome.value}")
        totale = self.model.record(selected_row).value(f"{FieldsEnum.Totale.value}")
        self.data = oggetti_data
        self.nome_bozza = nome_bozza
        self.totale = totale
        super().accept()

    def filter_bozze(self, text):
        if not text:
            self.model.setFilter("")
            return
        filter_str = f"{FieldsEnum.Nome.value} LIKE '%{text}%'"
        self.model.setFilter(filter_str)
        self.model.select()

    def cancella_bozza(self):
        selected_indexes = self.tableViewBozzeAcquisti.selectionModel().selectedRows()
        if not selected_indexes:
            msg = createMessageBox("Errore", "Seleziona una bozza da cancellare.")
            msg.exec_()
            return
        selected_row = selected_indexes[0].row()
        record_id = self.model.record(selected_row).value(f"{FieldsEnum.ID_Bozza_Acquisto.value}")
        msg_confirm = createMessageBox(
            "Conferma Cancellazione",
            "Sei sicuro di voler cancellare questa bozza? Questa azione non può essere annullata.",
            QtWidgets.QMessageBox.Warning,
            buttons=[QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No],
        )
        if msg_confirm.exec_() != QtWidgets.QMessageBox.Yes:
            return
        query = QtSql.QSqlQuery(self.main_db)
        query.prepare(f"DELETE FROM {DBTables.BOZZE_ACQUISTI.value} WHERE {FieldsEnum.ID_Bozza_Acquisto.value} = ?")
        query.addBindValue(record_id)
        if not query.exec_():
            print(
                "Errore durante la cancellazione della bozza:", query.lastError().text()
            )
            msg = createMessageBox(
                "Errore", "Errore durante la cancellazione della bozza."
            )
            msg.exec_()
        self.model.select()

    def svuota_bozze(self):
        msg_confirm = createMessageBox(
            "Conferma Svuotamento",
            "Sei sicuro di voler cancellare tutte le bozze? Questa azione non può essere annullata.",
            QtWidgets.QMessageBox.Warning,
            buttons=[QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No],
        )
        if msg_confirm.exec_() != QtWidgets.QMessageBox.Yes:
            return
        query = QtSql.QSqlQuery(self.main_db)
        if not query.exec_(f"DELETE FROM {DBTables.BOZZE_ACQUISTI.value}"):
            print("Errore durante lo svuotamento delle bozze:", query.lastError().text())
            msg = createMessageBox("Errore", "Errore durante lo svuotamento delle bozze.")
            msg.exec_()
        self.model.select()