from datetime import datetime
import os

from PyQt5 import QtWidgets, QtGui

from PyQt5.QtSql import QSqlTableModel
from .models.magazzino_model import MagazzinoModel
from icons import icons_rc  # noqa: F401
from utils import pulisci_testo, createMessageBox


class StoricoTabController:
    def __init__(self, ui):
        self.ui = ui
        self.fields = {"prezzo": "prezzo_vendita", "date": "sell_date"}

        self.model_magazzino = MagazzinoModel(self.ui.db_main)
        self.model_magazzino.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model_magazzino.setTable("sales")
        self.model_magazzino.select()

        self.ui.tableViewStorico.setModel(self.model_magazzino)
        self.ui.comboBoxCondizione_Storico.addItems(
            ["", "Mint", "Near Mint", "Lightly Played", "Played", "Poor"]
        )
        self.ui.comboBoxCondizione_Storico.currentTextChanged.connect(self.applica_filtri)

        self.ui.lineEditStoricoSearch.textChanged.connect(self.applica_filtri)

        self.ui.buttonGroupStorico.buttonClicked.connect(self.on_storico_changed)

        self.ui.doubleSpinBoxMinStorico.valueChanged.connect(self.on_price_changed)
        self.ui.doubleSpinBoxMaxStorico.valueChanged.connect(self.on_price_changed)

        self.ui.dateTimeEditStorico_A.setDateTime(datetime.now())
        self.ui.dateTimeEditStorico_A.dateTimeChanged.connect(self.on_date_changed)
        self.ui.dateTimeEditStorico_Da.dateTimeChanged.connect(self.on_date_changed)

    def applica_filtri(self, *args):
        try:
            filtri = []

            # TESTO
            testo = self.ui.lineEditStoricoSearch.text().strip()
            if testo:
                t = pulisci_testo(testo)
                filtri.append(f"""
                (espansione LIKE '%{t}%'
                OR nome LIKE '%{t}%'
                OR barcode LIKE '%{t}%')
                """)

            # CONDIZIONE
            condizione = self.ui.comboBoxCondizione_Storico.currentText()
            if condizione:
                filtri.append(f"condizione = '{condizione}'")

            # PREZZO
            min_val = self.ui.doubleSpinBoxMinStorico.value()
            max_val = self.ui.doubleSpinBoxMaxStorico.value()

            filtri.append(f"{self.fields['prezzo']} BETWEEN {min_val} AND {max_val}")

            # DATA
            data_from = self.ui.dateTimeEditStorico_Da.dateTime()
            data_to = self.ui.dateTimeEditStorico_A.dateTime()

            data_from_str = data_from.toString("yyyy-MM-dd HH:mm:ss")
            data_to_str = data_to.toString("yyyy-MM-dd HH:mm:ss")
            data_field = self.fields["date"]

            filtri.append(f"{data_field} BETWEEN '{data_from_str}' AND '{data_to_str}'")

            filtro_finale = " AND ".join(filtri)

            print(filtro_finale)
            self.model_magazzino.setFilter(filtro_finale)
            self.model_magazzino.select()

        except Exception as e:
            msg = createMessageBox("Errore", f"Si è verificato un errore: {str(e)}")
            msg.exec_()


    def on_storico_changed(self, button):
        table_mapping = {"Vendite": "sales", "Acquisti": "purchase"}
        field_mapping = {"Vendite": {"prezzo": "prezzo_vendita", "date": "sell_date"},
                         "Acquisti": {"prezzo": "prezzo_acquisto", "date": "purchase_date"}}

        self.fields = {"prezzo": field_mapping[button.text()]["prezzo"],
                       "date": field_mapping[button.text()]["date"]}
        self.model_magazzino.setTable(table_mapping.get(button.text()))
        self.model_magazzino.select()

        self.applica_filtri()

    def update_spin_limits(self):
        min_val = self.ui.doubleSpinBoxMinStorico.value()
        max_val = self.ui.doubleSpinBoxMaxStorico.value()

        # il max non può scendere sotto il min
        self.ui.doubleSpinBoxMaxStorico.setMinimum(min_val)

        # il min non può salire sopra il max
        self.ui.doubleSpinBoxMinStorico.setMaximum(max_val)

    def on_price_changed(self):
        self.update_spin_limits()
        self.applica_filtri()

    def update_date_limits(self):
        data_from = self.ui.dateTimeEditStorico_Da.dateTime()
        data_to = self.ui.dateTimeEditStorico_A.dateTime()

        # vincoli UI
        self.ui.dateTimeEditStorico_A.setMinimumDateTime(data_from)
        self.ui.dateTimeEditStorico_Da.setMaximumDateTime(data_to)

        # correzione se invertito
        if data_from > data_to:
            self.ui.dateTimeEditStorico_A.setDateTime(data_from)

    def on_date_changed(self):
        self.update_date_limits()
        self.applica_filtri()