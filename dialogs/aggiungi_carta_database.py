from PyQt5 import QtWidgets, uic, QtSql
from config import get_resource_path, database_table
from utils import createMessageBox
import os
import traceback


class AggiungiCartaDatabaseDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__()
        self.data = data
        self.db_cards = QtSql.QSqlDatabase.database("card_db_connection")
        # Carica il file .ui
        uic.loadUi(
            get_resource_path(os.path.join("ui", "dialog_aggiungi_carta.ui")), self
        )

    def accept(self):
        card_data = {
            "id": self.lineEditID.text().strip(),
            "name": self.lineEditNome.text().strip(),
            "espansione_id": self.lineEditEspansioneID.text().strip(),
            "espansione_nome": self.lineEditEspansioneNome.text().strip(),
            "image": self.lineEditImageURL.text().strip(),
            "pricing_cardmarket": self.doubleSpinBox.value(),
        }
        if not all(list(card_data.values())):
            msg = createMessageBox(
                "Errore", "Compila tutti i campi prima di aggiungere la carta."
            )
            msg.exec_()
            return
        try:
            insert_query = QtSql.QSqlQuery(self.db_cards)
            print(card_data)
            insert_query.prepare(f"""
                INSERT INTO {database_table} (id, name, espansione_id, espansione_nome, image, pricing_cardmarket_low)
                VALUES (:id, :name, :espansione_id, :espansione_nome, :image, :pricing_cardmarket_low)
            """)
            insert_query.bindValue(":id", card_data["id"])
            insert_query.bindValue(":name", card_data["name"])
            insert_query.bindValue(":espansione_id", card_data["espansione_id"])
            insert_query.bindValue(":espansione_nome", card_data["espansione_nome"])
            insert_query.bindValue(":image", card_data["image"])
            insert_query.bindValue(
                ":pricing_cardmarket_low", card_data["pricing_cardmarket"]
            )
            if not insert_query.exec_():
                msg = createMessageBox(
                    "Errore",
                    f"Errore durante l'inserimento della carta: {insert_query.lastError().text()}",
                )
                msg.exec_()
                return
            self.db_cards.commit()
            msg = createMessageBox(
                "Successo", "Carta aggiunta con successo al database!"
            )
            msg.exec_()
        except Exception as e:
            self.db_cards.rollback()
            msg = createMessageBox(
                "Errore",
                f"Errore durante l'inserimento della carta:\n{str(e)}",
                QtWidgets.QMessageBox.Critical,
            )
            msg.exec_()
            traceback.print_exc()
            return

        super().accept()
