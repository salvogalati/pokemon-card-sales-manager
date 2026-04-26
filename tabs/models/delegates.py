from PyQt5.QtWidgets import QItemDelegate, QComboBox
from PyQt5.QtCore import Qt
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