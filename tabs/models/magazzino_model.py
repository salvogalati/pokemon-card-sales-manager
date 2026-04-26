from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor



class MagazzinoModel(QSqlTableModel):
    def __init__(self, db, parent=None):
        super().__init__(parent, db)

    def flags(self, index):
        flags = super().flags(index)

        # esempio: colonne 0 e 2 NON editabili
        if index.column() in [0]:
            return flags & ~Qt.ItemIsEditable

        return flags

    # def data(self, index, role=Qt.DisplayRole):
    #     col = self.fieldIndex("da_prezzare")
    #     value = super().data(index, Qt.EditRole)

    #     if index.column() == col:

    #         # if role == Qt.DisplayRole:
    #         #     return value  # già "Si" / "No"

    #         if role == Qt.BackgroundRole:
    #             if value == "Si":
    #                 return QColor("#e7f34b")

    #     return super().data(index, role)

    def data(self, index, role=Qt.DisplayRole):
        col = self.fieldIndex("da_prezzare")
        value = super().data(index, Qt.EditRole)

        if index.column() == col:
            if role == Qt.DisplayRole:
                return value  # "Si" / "No"

            if role == Qt.BackgroundRole:
                if value == "Si":
                    return QColor("#e7f34b")
                else:
                    pass
                    #print(index.row(), value)

        return super().data(index, role)



