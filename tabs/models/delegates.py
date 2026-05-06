from PyQt5.QtWidgets import QItemDelegate, QComboBox, QStyledItemDelegate
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from config import cards_condizioni

class YesNoDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(["No", "Si"])
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText("Si" if value in (1, True, "1") else "No")

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
        model.dataChanged.emit(index, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class CondizioneComboBoxDelegate(QItemDelegate):
    def createEditor(self, parent, option, index):
        combo = QComboBox(parent)
        combo.addItems(cards_condizioni)
        return combo

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
        model.dataChanged.emit(index, index)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class CenterIconDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        option = option.__class__(option)  # copia sicura

        icon = index.data(Qt.DecorationRole)
        text = index.data(Qt.DisplayRole)

        painter.save()

        rect = option.rect

        # centro area
        center_x = rect.x() + rect.width() // 2
        center_y = rect.y() + rect.height() // 2

        # disegna icona centrata
        if isinstance(icon, QIcon):
            pixmap = icon.pixmap(60, 60)
            x = center_x - pixmap.width() // 2
            y = center_y - pixmap.height() // 2
            painter.drawPixmap(x, y, pixmap)
        else:
            # fallback testo centrato
            painter.drawText(rect, Qt.AlignCenter, str(text))

        painter.restore()