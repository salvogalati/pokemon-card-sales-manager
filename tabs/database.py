import traceback

from PyQt5 import QtSql, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject, Qt
import requests

from .models.card_database_model import CardDatabaseModel
from dialogs.aggiungi_carta_database import AggiungiCartaDatabaseDialog
from utils import createMessageBox, pulisci_testo
from config import database_table
from icons import icons  # noqa: F401


class DatabaseTabController(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

        db_cards = QtSql.QSqlDatabase.database("card_db_connection")
        self.db = db_cards  # Assign the database connection to self.db
        self.model_card_database = CardDatabaseModel(db_cards)
        self.model_card_database.setTable(database_table)
        self.model_card_database.select()
        self.ui.tableViewDatabase.setModel(self.model_card_database)

        self.ui.tableViewDatabase.selectionModel().selectionChanged.connect(
            self.on_row_changed
        )

        self.ui.lineEditSearchDatabase.textChanged.connect(self.filtra_tabella)
        self.ui.buttonAggiungiCartaDatabase.clicked.connect(
            self.apri_dialog_aggiungi_carta
        )
        self.ui.buttonRimuoviCartaDatabase.clicked.connect(
            self.rimuovi_carta_selezionata
        )

    def filtra_tabella(self, testo):
        testo = pulisci_testo(testo)
        if not testo:
            self.model_card_database.setFilter("")
        else:
            filtro = f"""name LIKE '%{testo}%'
            OR espansione_nome LIKE '%{testo}%'
            OR id LIKE '%{testo}%'
            OR espansione_id LIKE '%{testo}%'"""
            self.model_card_database.setFilter(filtro)

    def on_row_changed(self, selected, deselected):
        indexes = selected.indexes()
        if not indexes:
            return

        row = indexes[0].row()

        col_image = self.model_card_database.fieldIndex("image")
        index = self.model_card_database.index(row, col_image)

        image_url = self.model_card_database.data(index)
        if not image_url:
            url = "https://www.affaridanerd.it/wp-content/uploads/2023/12/Pokemon-TCG-retro-carta.png"
            pixmap = self.load_image(url)
            if pixmap:
                self.ui.labelCartaImmagineDatabase.setPixmap(
                    pixmap.scaled(
                        self.ui.labelCartaImmagineDatabase.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            return

        pixmap = self.load_image(image_url + "/high.png")

        if pixmap:
            self.ui.labelCartaImmagineDatabase.setPixmap(
                pixmap.scaled(
                    self.ui.labelCartaImmagineDatabase.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    def load_image(self, url):
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            image = QPixmap()
            image.loadFromData(response.content)
            return image

        except Exception:
            return None

    def apri_dialog_aggiungi_carta(self):
        dialog = AggiungiCartaDatabaseDialog({}, self.ui)
        if dialog.exec_():
            self.model_card_database.select()

    def rimuovi_carta_selezionata(self):
        selected_indexes = self.ui.tableViewDatabase.selectionModel().selectedIndexes()
        rows = set(index.row() for index in selected_indexes)
        if not rows:
            msg = createMessageBox("Errore", "Seleziona una carta da rimuovere.")
            msg.exec_()
            return
        selected_row = list(rows)[0]
        card_id_index = self.model_card_database.index(
            selected_row, self.model_card_database.fieldIndex("id")
        )
        card_id = self.model_card_database.data(card_id_index)

        confirm_msg = createMessageBox(
            "Conferma Rimozione",
            f"Sei sicuro di voler rimuovere la carta con ID '{card_id}' dal database?",
            QtWidgets.QMessageBox.Warning,
            [
                QtWidgets.QMessageBox.StandardButton.Yes,
                QtWidgets.QMessageBox.StandardButton.No,
            ],
        )
        risposta = confirm_msg.exec_()
        if risposta == QtWidgets.QMessageBox.StandardButton.No:
            return
        try:
            delete_query = QtSql.QSqlQuery(self.db)
            delete_query.prepare(f"DELETE FROM {database_table} WHERE id = ?")
            delete_query.addBindValue(card_id)
            if not delete_query.exec_():
                msg = createMessageBox(
                    "Errore",
                    f"Errore durante la rimozione della carta: {delete_query.lastError().text()}",
                    QtWidgets.QMessageBox.Critical,
                )
                msg.exec_()
                return
            self.model_card_database.select()
            msg = createMessageBox(
                "Successo", "Carta rimossa con successo dal database!"
            )
            msg.exec_()
        except Exception as e:
            self.db.rollback()
            msg = createMessageBox(
                "Errore",
                f"Errore durante la rimozione della carta:\n{str(e)}",
                QtWidgets.QMessageBox.Critical,
            )
            msg.exec_()
            traceback.print_exc()
            return
