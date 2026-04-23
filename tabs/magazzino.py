from datetime import datetime
import os

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtSql
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QTableView
from PyQt5.QtSql import QSqlQuery, QSqlTableModel
from .models.magazzino_model import MagazzinoModel, YesNoDelegate
from PyQt5.QtWidgets import QStyledItemDelegate, QSpinBox
from icons import icons_rc
from config import main_db, backup_folder
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
        self.model_magazzino.setTable("stock")
        self.model_magazzino.select()

        self.ui.tableViewMagazzino.setModel(self.model_magazzino)
        
    
        delegate = YesNoDelegate(self.ui.tableViewMagazzino)
        #self.ui.tableViewMagazzino.setItemDelegateForColumn(self.model_magazzino.fieldIndex("prezzo"), SpinBoxDelegate())
        self.ui.tableViewMagazzino.setItemDelegateForColumn(self.model_magazzino.fieldIndex("da_prezzare"), delegate)
        # query = QSqlQuery("SELECT DISTINCT condizione FROM stock")

        # unique_values_condizione = []
        # while query.next():
        #     unique_values_condizione.append(query.value(0))

        self.ui.comboBoxCondizione.addItems(["", "Mint", "Near Mint", "Lightly Played", "Played", "Poor"])

        self.ui.button_applica_filtro.clicked.connect(self.applica_filtro)
        self.ui.button_resetta_filtro.clicked.connect(self.resetta_filtro)
        self.ui.buttonMagazzinoSave.clicked.connect(self.salva_modifiche)
        self.ui.buttonMagazzinoRipristina.clicked.connect(self.ripristina_backup)

    def applica_filtro(self):
        filtro_nome = self.ui.lineEditMagazzinoFiltroNome.text()
        filtro_espansione = self.ui.lineEditMagazzinoFiltroEspansione.text()
        filtro_qty = self.ui.spinBoxMagazzinoQty.value()
        filtro_condizione = self.ui.comboBoxCondizione.currentText()
        filtro_prezzo_min = self.ui.doubleSpinBoxMagazzinoPrezzoMin.value()
        filtro_prezzo_max = self.ui.doubleSpinBoxMagazzinoPrezzoMax.value()

        filtro_sql = self.check_filtri(filtro_nome, filtro_espansione, filtro_qty, filtro_condizione, filtro_prezzo_min, filtro_prezzo_max)
        #☻print(filtro_sql)
        self.model_magazzino.setFilter(filtro_sql)

    @staticmethod
    def check_filtri(filtro_nome, filtro_espansione, filtro_qty, filtro_condizione, filtro_prezzo_min, filtro_prezzo_max):
        def escape_sql(value):
            return value.replace("'", "''")

        condizioni = []

        if filtro_nome.strip():
            nome = escape_sql(filtro_nome)
            condizioni.append(f"nome LIKE '%{nome}%'")

        if filtro_espansione.strip():
            esp = escape_sql(filtro_espansione)
            condizioni.append(f"espansione LIKE '%{esp}%'")

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
    
    def resetta_filtro(self):
        self.ui.lineEditMagazzinoFiltroNome.clear()
        self.ui.lineEditMagazzinoFiltroEspansione.clear()
        self.ui.spinBoxMagazzinoQty.setValue(0)
        self.ui.comboBoxCondizione.setCurrentIndex(0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMin.setValue(0.0)
        self.ui.doubleSpinBoxMagazzinoPrezzoMax.setValue(0.0)
        self.model_magazzino.setFilter("")

    def salva_modifiche(self):
        msg = self.createMessageBox("Conferma Salvataggio", "Sei sicuro di voler salvare le modifiche al magazzino?",
                                     QtWidgets.QMessageBox.Question, [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No])
        risposta = msg.exec_()
        if risposta == QMessageBox.No:
            return

        self.backup_database()
        if self.model_magazzino.submitAll():
            
            QMessageBox.information(self.ui, "Successo", "Modifiche salvate con successo!")
        else:
            QMessageBox.critical(self.ui, "Errore", f"Errore durante il salvataggio: {self.model_magazzino.lastError().text()}")

    def backup_database(self):
        try:
            date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            shutil.copy(os.path.join(os.path.dirname(__file__), main_db),
                         os.path.join(os.path.dirname(__file__), backup_folder, f"backup_pokemon_cards_{date_now}.db"))
            #QMessageBox.information(self.ui, "Backup", "Backup del database creato con successo!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Errore Backup", f"Errore durante il backup del databse\nAttenzione non sarà possibile ripristinare il database\nERRORE: {str(e)}")

    def ripristina_backup(self):
        backup_files = [f for f in os.listdir(os.path.join(os.path.dirname(__file__), backup_folder)) if f.startswith("backup_pokemon_cards_") and f.endswith(".db")]
        if not backup_files:
            QMessageBox.information(self.ui, "Nessun Backup", "Non sono stati trovati file di backup.")
            return
        backup_to_restore = backup_files[-1]  # Prendi l'ultimo backup creato
        data_backup = backup_to_restore.replace("backup_pokemon_cards_", "").replace(".db", "")
        msg = self.createMessageBox("Conferma Ripristino", f"Sei sicuro di voler ripristinare il database dal backup più recente effettuato il {data_backup}?",
                                     QtWidgets.QMessageBox.Warning, [QMessageBox.StandardButton.Yes, QMessageBox.StandardButton.No])
        risposta = msg.exec_()
        
        if risposta == QMessageBox.No:
            return
        try:
            shutil.copy(os.path.join(os.path.dirname(__file__), backup_folder, backup_to_restore),
                         os.path.join(os.path.dirname(__file__), main_db))
            self.model_magazzino.select()  # Ricarica i dati nel modello
            QMessageBox.information(self.ui, "Ripristino", "Database ripristinato con successo dal backup!")
        except Exception as e:
            QMessageBox.critical(self.ui, "Errore Ripristino", f"Errore durante il ripristino del database\nERRORE: {str(e)}")

    def createMessageBox(self, title, text, icon=QtWidgets.QMessageBox.Information , buttons=[]):
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(icon)
        msg.setWindowIcon(QtGui.QIcon("icons/logo_kingdom_cards.png"))
        for button in buttons:
            msg.addButton(button)
        return msg