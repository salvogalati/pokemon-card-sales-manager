import json
import os
from PyQt5 import QtWidgets, uic, QtSql
from config import DBTables, FieldsEnum, get_resource_path
from utils import createMessageBox


class SalvaBozzaAcquistiDialog(QtWidgets.QDialog):
    def __init__(self, data, parent=None):
        super().__init__()
        self.data = data

        # Carica il file .ui
        uic.loadUi(get_resource_path(os.path.join("ui", "dialog_salva_bozza.ui")), self)

        self.main_db = parent.db_main

        # Connetti i pulsanti
        self.saveButton.clicked.connect(self.salva_bozza)
        self.cancelButton.clicked.connect(self.reject)

    def salva_bozza(self):
        nome_cliente = self.lineEditNome.text().strip()

        data = json.loads(self.data)
        if not nome_cliente:
            msg = createMessageBox("Errore", "Il nome del cliente è obbligatorio.")
            msg.exec_()
            return
        prezzo_totale = sum(float(item[FieldsEnum.Prezzo_Acquisto.value]) for item in data)
        # Salva la bozza nel database
        query = QtSql.QSqlQuery(self.main_db)
        query.prepare(
            f"INSERT INTO {DBTables.BOZZE_ACQUISTI.value} ({FieldsEnum.Nome.value}, {FieldsEnum.Numero_oggetti.value}, {FieldsEnum.Totale.value}, {FieldsEnum.Oggetti.value}) VALUES (:nome, :num, :tot, :ogg)"
        )
        query.bindValue(":nome", nome_cliente)
        query.bindValue(":num", len(data))
        query.bindValue(":tot", prezzo_totale)
        query.bindValue(":ogg", self.data)
        if not query.exec_():
            print("Errore durante l'inserimento della bozza:", query.lastError().text())
            print("Query:", query.executedQuery())
            msg = createMessageBox(
                "Errore", "Errore durante il salvataggio della bozza."
            )
            msg.exec_()
        else:
            msg = createMessageBox("Successo", "Bozza salvata con successo!")
            msg.exec_()
            self.accept()

    def update_bozza(self, data, name):
        data = json.loads(data)
        prezzo_totale = sum(float(item[FieldsEnum.Prezzo_Acquisto.value]) for item in data)
        query = QtSql.QSqlQuery(self.main_db)
        query.prepare(
            f"UPDATE {DBTables.BOZZE_ACQUISTI.value} SET {FieldsEnum.Nome.value} = :nome, {FieldsEnum.Numero_oggetti.value} = :num, {FieldsEnum.Totale.value} = :tot, {FieldsEnum.Oggetti.value} = :ogg WHERE {FieldsEnum.Nome.value} = :nome"
        )
        query.bindValue(":nome", name)
        query.bindValue(":num", len(data))
        query.bindValue(":tot", prezzo_totale)
        query.bindValue(":ogg", json.dumps(data))

        if not query.exec_():
            print("Errore durante l'aggiornamento della bozza:", query.lastError().text())
            msg = createMessageBox("Errore", "Errore durante l'aggiornamento della bozza.",
                                   icon=QtWidgets.QMessageBox.Critical)
            msg.exec_()
        elif query.numRowsAffected() == 0:
            print(f"Nessuna bozza trovata con nome: {name}")
            msg = createMessageBox("Errore", f"Nessuna bozza trovata con nome '{name}'.\
                                    \nSalvataggio non completato", icon=QtWidgets.QMessageBox.Warning)
            msg.exec_()
        else:
            msg = createMessageBox("Successo", "Bozza aggiornata con successo!")
            msg.exec_()
            self.accept()
