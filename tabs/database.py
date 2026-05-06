
from PyQt5 import QtSql
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QObject, Qt
import requests

from .models.card_database_model import CardDatabaseModel
from utils import createMessageBox
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

        self.ui.tableViewDatabase.selectionModel().selectionChanged.connect(self.on_row_changed)

        self.ui.lineEditSearchDatabase.textChanged.connect(self.filtra_tabella)

    def filtra_tabella(self, testo):
        if not testo:
            self.model_card_database.setFilter("")
        else:
            filtro = f"nome LIKE '%{testo}%' OR espansione LIKE '%{testo}%'"
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
                         Qt.SmoothTransformation
                     )
                 )
             return

        pixmap = self.load_image(image_url + "/high.png")

        if pixmap:
            self.ui.labelCartaImmagineDatabase.setPixmap(
                pixmap.scaled(
                    self.ui.labelCartaImmagineDatabase.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
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