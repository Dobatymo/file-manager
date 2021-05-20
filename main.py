import subprocess
import sys

from PySide6 import QtCore, QtWidgets, QtGui

def get_model():
	rows = 1
	cols = 3
	model = QtGui.QStandardItemModel(rows, cols)
	model.setHorizontalHeaderLabels(["a", "b", "c"]);

	currentrow = 0
	for t, b, s in [("1", "2", "3")]:
		model.setItem(currentrow, 0, QtGui.QStandardItem(t))
		model.setItem(currentrow, 1, QtGui.QStandardItem(b))
		model.setItem(currentrow, 2, QtGui.QStandardItem(s))
		currentrow += 1

def get_model_b():
	model = QtWidgets.QFileSystemModel()
	model.setRootPath(QtCore.QDir.currentPath())
	return model

class MyWidget(QtWidgets.QWidget):
	def __init__(self):
		super().__init__()

		self.table = QtWidgets.QTableView()
		self.table.setSortingEnabled(True)
		self.table.setShowGrid(False)
		self.table.verticalHeader().setVisible(False)

		model = get_model_b()
		self.table.setModel(model)

		self.layout = QtWidgets.QVBoxLayout(self)
		self.layout.addWidget(self.table)

		self.table.activated.connect(self.activated)

	@QtCore.Slot()
	def activated(self, event: QtCore.QModelIndex):
		model = event.model()
		if model.isDir(event):
			self.table.setRootIndex(event)
		else:
			path = model.filePath(event)
			subprocess.Popen(path, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

if __name__ == "__main__":
	app = QtWidgets.QApplication([])

	widget = MyWidget()
	widget.resize(800, 600)
	widget.show()

	sys.exit(app.exec())
