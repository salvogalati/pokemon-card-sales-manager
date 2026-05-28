from PyQt5.QtSql import QSqlTableModel
from config import card_condizioni_icons
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from icons import icons  # noqa: F401


class CardDatabaseModel(QSqlTableModel):
    def __init__(self, db, parent=None):
        super().__init__(parent, db)

    def flags(self, index):
        return super().flags(index)

    def data(self, index, role=Qt.DisplayRole):
        value = super().data(index, Qt.EditRole)
        if role == Qt.TextAlignmentRole:
            return Qt.AlignCenter
        if index.column() == self.fieldIndex("condition"):
            # color = card_condizioni_colors.get(value, None)
            # if role == Qt.BackgroundRole:
            #     return QColor(color)
            # if role == Qt.DisplayRole:
            #     return "CIAO"
            if role == Qt.DecorationRole:
                icon_path = card_condizioni_icons.get(value, None)
                if icon_path:
                    return QIcon(icon_path)

        return super().data(index, role)
