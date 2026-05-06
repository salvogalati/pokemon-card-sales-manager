from datetime import datetime
import os

from PyQt5 import QtWidgets
from PyQt5 import QtSql
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtCore import QSize

from utils import pulisci_testo, createMessageBox
from .models.magazzino_model import MagazzinoModel
from .models.delegates import YesNoDelegate, CondizioneComboBoxDelegate
from PyQt5.QtWidgets import QStyledItemDelegate, QSpinBox
from icons import icons  # noqa: F401
from config import main_db, backup_folder, cards_condizioni, get_resource_path, stock_table
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

        db = QtSql.QSqlDatabase.database("main_connection")
        self.model_magazzino = MagazzinoModel(db)
        self.model_magazzino.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.model_magazzino.setTable(stock_table)
        self.model_magazzino.select()

        self.ui.tableViewMagazzino.setModel(self.model_magazzino)

        delegateYesNo = YesNoDelegate(self.ui.tableViewMagazzino)
        # self.ui.tableViewMagazzino.setItemDelegateForColumn(self.model_magazzino.fieldIndex("prezzo"), SpinBoxDelegate())
        self.ui.tableViewMagazzino.setItemDelegateForColumn(
            self.model_magazzino.fieldIndex("da_prezzare"), delegateYesNo
        )
        delegateCondizione = CondizioneComboBoxDelegate(self.ui.tableViewMagazzino)
        self.ui.tableViewMagazzino.setItemDelegateForColumn(
            self.model_magazzino.fieldIndex("condizione"), delegateCondizione
        )
        self.ui.tableViewMagazzino.setIconSize(QSize(60, 60))
        # query = QSqlQuery("SELECT DISTINCT condizione FROM stock")

        # unique_values_condizione = []
        # while query.next():
        #     unique_values_condizione.append(query.value(0))

        self.ui.comboBoxCondizione.addItems(
            [""] + cards_condizioni
        )

        self.ui.button_applica_filtro.clicked.connect(self.applica_filtro)
        self.ui.button_resetta_filtro.clicked.connect(self.resetta_filtro)
        self.ui.buttonMagazzinoSave.clicked.connect(self.salva_modifiche)
        self.ui.buttonMagazzinoRipristina.clicked.connect(self.ripristina_backup)

        self.ui.lineEditSearchMagazzino.textChanged.connect(self.filtra_tabella_search)

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
        # ☻print(filtro_sql)
        self.model_magazzino.setFilter(filtro_sql)

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
            condizioni.append(f"name LIKE '%{nome}%'")

        if filtro_espansione.strip():
            esp = escape_sql(filtro_espansione)
            condizioni.append(f"espansione_id LIKE '%{esp}%' OR espansione_nome LIKE '%{esp}%'")

        if filtro_qty > 0:
            condizioni.append(f"quantita_stock >= {filtro_qty}")

        if filtro_condizione:
            cond = escape_sql(filtro_condizione)
            condizioni.append(f"condizione = '{cond}'")

        if filtro_prezzo_min > 0:
            condizioni.append(f"prezzo >= {filtro_prezzo_min}")

        if filtro_prezzo_max > 0:
            condizioni.append(f"prezzo <= {filtro_prezzo_max}")

        return " AND ".join(condizioni)

    def filtra_tabella_search(self, testo):
        if not testo:
            self.model_magazzino.setFilter("")
            self.model_magazzino.select()
            return
        testo_sicuro = pulisci_testo(testo)

        filtro = f"""
        espansione_id LIKE '%{testo_sicuro}%'
        OR espansione_nome LIKE '%{testo_sicuro}%'
        OR name LIKE '%{testo_sicuro}%'
        OR barcode LIKE '%{testo_sicuro}%'
        OR condizione LIKE '%{testo_sicuro}%'
        """

        self.model_magazzino.setFilter(filtro)
        self.model_magazzino.select()

    def resetta_filtro(self):
        self.ui.lineEditMagazzinoFiltroNome.clear()
        self.ui.lineEditMagazzinoFiltroEspansione.clear()
        self.ui.spinBoxMagazzinoQty.setValue(0)
        self.ui.comboBoxCondizione.setCurrentIndex(0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMin.setValue(0.0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMax.setValue(0.0)
        self.model_magazzino.setFilter("")

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
        if self.model_magazzino.submitAll():
            QMessageBox.information(
                self.ui, "Successo", "Modifiche salvate con successo!"
            )
        else:
            QMessageBox.critical(
                self.ui,
                "Errore",
                f"Errore durante il salvataggio: {self.model_magazzino.lastError().text()}",
            )

    def backup_database(self):
        try:
            date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_dir = get_resource_path(backup_folder)
            os.makedirs(backup_dir, exist_ok=True)
            shutil.copy(
                get_resource_path(main_db),
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
        backup_dir = get_resource_path(backup_folder)
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
                get_resource_path(main_db),
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
