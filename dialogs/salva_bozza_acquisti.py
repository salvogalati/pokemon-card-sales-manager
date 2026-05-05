import json
import os
import sys
from PyQt5 import QtWidgets, uic, QtSql
from config import get_resource_path
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
        prezzo_totale = sum(float(item["prezzo_acquisto"]) for item in data)
        # Salva la bozza nel database
        query = QtSql.QSqlQuery(self.main_db)
        query.prepare("INSERT INTO draft_purchase (nome_cliente, numero_oggetti, totale, oggetti) VALUES (:nome, :num, :tot, :ogg)")
        query.bindValue(":nome", nome_cliente)
        query.bindValue(":num", len(data))
        query.bindValue(":tot", prezzo_totale)
        query.bindValue(":ogg", self.data)
        if not query.exec_():
            print("Errore durante l'inserimento della bozza:", query.lastError().text())
            print("Query:", query.executedQuery())
            msg = createMessageBox("Errore", "Errore durante il salvataggio della bozza.")
            msg.exec_()
        else:
            self.accept()