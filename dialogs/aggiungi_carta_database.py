from PyQt5 import QtWidgets, uic, QtSql
from config import get_resource_path, DBTables, FieldsEnum
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
            FieldsEnum.ID_Cardmarket.value: self.lineEditID.text().strip(),
            FieldsEnum.Nome.value: self.lineEditNome.text().strip(),
            FieldsEnum.Espansione_ID.value: self.lineEditEspansioneID.text().strip(),
            FieldsEnum.Espansione.value: self.lineEditEspansioneNome.text().strip(),
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
                INSERT INTO {DBTables.DATABASE_CARDS.value} ({FieldsEnum.ID_Cardmarket.value}, {FieldsEnum.Nome.value}, {FieldsEnum.Espansione_ID.value}, '{FieldsEnum.Espansione.value}')
                VALUES (:id, :name, :espansione_id, :espansione_nome)
            """)
            insert_query.bindValue(":id", card_data[FieldsEnum.ID_Cardmarket.value])
            insert_query.bindValue(":name", card_data[FieldsEnum.Nome.value])
            insert_query.bindValue(":espansione_id", card_data[FieldsEnum.Espansione_ID.value])
            insert_query.bindValue(":espansione_nome", card_data[FieldsEnum.Espansione.value])
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
