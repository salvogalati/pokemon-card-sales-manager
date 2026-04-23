from PyQt5.QtSql import QSqlTableModel

class CardDatabaseModel(QSqlTableModel):
    def __init__(self, db, parent=None):
        super().__init__(parent, db)

    def flags(self, index):
        return super().flags(index)