from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtCore import Qt

class MagazzinoModel(QSqlTableModel):
    def flags(self, index):
        flags = super().flags(index)

        # esempio: colonne 0 e 2 NON editabili
        if index.column() in [0]:
            return flags & ~Qt.ItemIsEditable

        return flags