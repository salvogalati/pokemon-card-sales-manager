from PyQt5.QtSql import QSqlTableModel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon
from config import card_condizioni_colors, card_condizioni_icons
from icons import icons  # noqa: F401


class MagazzinoModel(QSqlTableModel):
    def __init__(self, db, parent=None):
        super().__init__(parent, db)

    def flags(self, index):
        flags = super().flags(index)

        # esempio: colonne 0 e 2 NON editabili
        if index.column() in [0]:
            return flags & ~Qt.ItemIsEditable

        return flags

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
                    # print(index.row(), value)
        if index.column() == self.fieldIndex("condizione"):
            color = card_condizioni_colors.get(value, None)
            # if role == Qt.BackgroundRole:
            #     return QColor(color)
            if role == Qt.DisplayRole:
                return None
            if role == Qt.DecorationRole:
                icon_path = card_condizioni_icons.get(value, None)
                if icon_path:
                    return QIcon(icon_path)

        return super().data(index, role)
