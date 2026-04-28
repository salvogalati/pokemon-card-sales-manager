from PyQt5.QtSql import QSqlTableModel
from config import card_condizioni_colors
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

class CardDatabaseModel(QSqlTableModel):
    def __init__(self, db, parent=None):
        super().__init__(parent, db)

    def flags(self, index):
        return super().flags(index)
    
    def data(self, index, role=Qt.DisplayRole):
        value = super().data(index, Qt.EditRole)
        #print(index.column(),  self.fieldIndex("condizione"))
        if index.column() == self.fieldIndex("condizione"):
            color = card_condizioni_colors.get(value, None)
            if role == Qt.BackgroundRole:
                return QColor(color)
    

        return super().data(index, role)
