import traceback

from PyQt5 import QtSql, QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject, Qt
import requests

from .models.card_database_model import CardDatabaseModel
from dialogs.aggiungi_carta_database import AggiungiCartaDatabaseDialog
from utils import createMessageBox, pulisci_testo, auto_size_table_columns
from config import FieldsEnum, DBTables
from icons import icons  # noqa: F401


class DatabaseTabController(QObject):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

        db_cards = QtSql.QSqlDatabase.database("card_db_connection")
        self.db = db_cards  # Assign the database connection to self.db
        self.model_card_database = CardDatabaseModel(db_cards)
        self.model_card_database.setTable(DBTables.DATABASE_CARDS.value)
        self.model_card_database.select()
        self.ui.tableViewDatabase.setModel(self.model_card_database)

        self.ui.tableViewDatabase.selectionModel().selectionChanged.connect(
            self.on_row_changed
        )

        for col in range(self.model_card_database.columnCount()):
            field_name = self.model_card_database.headerData(col, Qt.Horizontal)
            if field_name not in [e.value for e in FieldsEnum]:
                pass
                #elf.ui.tableViewMagazzino.hideColumn(col)
            else:
                field_name_ok = FieldsEnum(field_name).name.replace("_", " ")
                self.model_card_database.setHeaderData(col, Qt.Horizontal, field_name_ok)

        self.ui.lineEditSearchDatabase.textChanged.connect(self.filtra_tabella)
        self.ui.buttonAggiungiCartaDatabase.clicked.connect(
            self.apri_dialog_aggiungi_carta
        )
        self.ui.buttonRimuoviCartaDatabase.clicked.connect(
            self.rimuovi_carta_selezionata
        )

        auto_size_table_columns(self.ui.tableViewDatabase, padding=30)

    def filtra_tabella(self, testo):
        testo = pulisci_testo(testo)
        if not testo:
            self.model_card_database.setFilter("")
        else:
            filtro = f"""{FieldsEnum.Nome.value} LIKE '%{testo}%'
            OR '{FieldsEnum.Espansione.value}' LIKE '%{testo}%'
            OR {FieldsEnum.Espansione_ID.value} LIKE '%{testo}%'
            OR {FieldsEnum.ID_Cardmarket.value} LIKE '%{testo}%'"""
            self.model_card_database.setFilter(filtro)

    def on_row_changed(self, selected, deselected):
        generic_url = "https://product-images.s3.cardmarket.com/51/SET/ID/ID.jpg"
        indexes = selected.indexes()
        if not indexes:
            return

        row = indexes[0].row()

        cardmarket_id_col = self.model_card_database.fieldIndex(FieldsEnum.ID_Cardmarket.value)
        index_cardmarket_id = self.model_card_database.index(row, cardmarket_id_col)
        cardmarket_id = self.model_card_database.data(index_cardmarket_id)

        set_id_col = self.model_card_database.fieldIndex(FieldsEnum.Espansione_ID.value)
        index_set_id = self.model_card_database.index(row, set_id_col)
        set_id = self.model_card_database.data(index_set_id)

        image_url = generic_url.replace("ID", str(cardmarket_id)).replace("SET", str(set_id))

        if not cardmarket_id:
            pixmap = self.load_image(":/images/images/Pokemon-TCG-retro-carta.png", local_path= True)
            if pixmap:
                self.ui.labelCartaImmagineDatabase.setPixmap(
                    pixmap.scaled(
                        self.ui.labelCartaImmagineDatabase.size(),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
            return

        pixmap = self.load_image(image_url)

        if pixmap:
            self.ui.labelCartaImmagineDatabase.setPixmap(
                pixmap.scaled(
                    self.ui.labelCartaImmagineDatabase.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )

    def load_image(self, url, local_path=None):
        if local_path:
            pixmap = QPixmap(url)
            if not pixmap.isNull():
                return pixmap
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.cardmarket.com/"
            }
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()

            image = QPixmap()
            image.loadFromData(response.content)
            return image

        except Exception:
            print(f"Errore durante il caricamento dell'immagine da {url}")
            print(traceback.format_exc())
            return QPixmap(":/images/images/Pokemon-TCG-retro-carta.png")

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
            selected_row, self.model_card_database.fieldIndex(FieldsEnum.ID_Cardmarket.value)
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
            delete_query.prepare(f"DELETE FROM {DBTables.DATABASE_CARDS.value} WHERE {FieldsEnum.ID_Cardmarket.value} = ?")
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
