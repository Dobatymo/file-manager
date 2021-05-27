import subprocess
import sys
import logging

from PySide6 import QtCore, QtWidgets, QtGui

logger = logging.getLogger(__name__)

def get_model(root):
	rows = 1
	cols = 3
	model = QtGui.QStandardItemModel(rows, cols)
	model.setHorizontalHeaderLabels(["a", "b", "c"])

	currentrow = 0
	for t, b, s in [("1", "2", "3")]:
		model.setItem(currentrow, 0, QtGui.QStandardItem(t))
		model.setItem(currentrow, 1, QtGui.QStandardItem(b))
		model.setItem(currentrow, 2, QtGui.QStandardItem(s))
		currentrow += 1

def get_model_b(root):
	model = QtWidgets.QFileSystemModel()
	model.setRootPath(root)
	return model

class FileManagerView(QtWidgets.QTableView):

	middle_clicked = QtCore.Signal(QtCore.QModelIndex)

	def __init__(self, parent):
		super().__init__(parent)
		self.setSortingEnabled(True)
		self.setShowGrid(False)
		self.verticalHeader().setVisible(False)
		self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
		self.setEditTriggers(QtWidgets.QAbstractItemView.SelectedClicked | QtWidgets.QAbstractItemView.EditKeyPressed)

		self.activated.connect(self.handle_activated)
		self.middle_clicked.connect(self.handle_middle_clicked)

		self.action_open = QtGui.QAction("Open", self)
		self.action_open.triggered.connect(self.handle_action_open)
		self.action_open_new = QtGui.QAction("Open in new window", self)
		self.action_open_new.triggered.connect(self.handle_action_open_new)
		self.action_open_default = QtGui.QAction("Open in default application", self)
		self.action_open_default.triggered.connect(self.handle_action_open_default)

	def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
		if event.button() == QtCore.Qt.MouseButton.MiddleButton:
			index = self.indexAt(event.pos())
			model = index.model()
			if model:
				self.middle_clicked.emit(index)
				return

		super().mouseReleaseEvent(event)

	@QtCore.Slot()
	def handle_activated(self, event: QtCore.QModelIndex):
		model = event.model()
		if model.isDir(event):
			self.setRootIndex(event)
		else:
			path = model.filePath(event)
			subprocess.Popen(path, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)

	@QtCore.Slot()
	def handle_middle_clicked(self, event: QtCore.QModelIndex):
		wm.create(MyWidget(event.model(), event))

	@QtCore.Slot()
	def handle_action_open(self, event):
		print(event)

	@QtCore.Slot()
	def handle_action_open_new(self, event):
		print(event)
		wm.create(MyWidget())

	@QtCore.Slot()
	def handle_action_open_default(self, event):
		print(event)

	def contextMenuEvent(self, event: QtGui.QContextMenuEvent):

		index = self.indexAt(event.pos())  # fixme: DeprecationWarning: Function: 'pos() const' is marked as deprecated, please check the documentation for more information.

		model = index.model()

		if model: # click on item
			menu = QtWidgets.QMenu(self)
			if model.isDir(index):
				menu.addAction(self.action_open)
				menu.addAction(self.action_open_new)
			else:
				menu.addAction(self.action_open_default)
			menu.exec(event.globalPos())
		else: # click on empty space
			pass

class MyWidget(QtWidgets.QWidget):
	def __init__(self, model, index=None):
		super().__init__()

		self.model = model

		if index:
			title = self.model.filePath(index)
		else:
			title = "Computer"

		self.action_up = QtGui.QAction("Up", self)
		self.action_up.triggered.connect(self.handle_action_up)
		self.action_back = QtGui.QAction("Back", self)
		self.action_back.triggered.connect(self.handle_action_back)

		self.table = FileManagerView(self)
		toolbar = QtWidgets.QToolBar()
		toolbar.addAction(self.action_up)
		toolbar.addAction(self.action_back)

		self.table.setModel(self.model)
		if index:
			self.table.setRootIndex(index)

		self.layout = QtWidgets.QVBoxLayout(self)
		self.layout.addWidget(self.table)
		self.layout.setMenuBar(toolbar)

		self.setWindowTitle(title)

	@QtCore.Slot()
	def handle_action_up(self, event):
		parent = self.model.parent(self.table.rootIndex())
		if parent:
			self.table.setRootIndex(parent)

	@QtCore.Slot()
	def handle_action_back(self, event):
		print(event)

class WindowManager:

	def __init__(self):
		self.widgets = []

	def create(self, widget):
		self.widgets.append(widget)
		widget.show()

if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	wm = WindowManager()

	root = QtCore.QDir.currentPath()
	logger.warning("Current path: %s", root)
	model = get_model_b(root)

	wm.create(MyWidget(model))

	sys.exit(app.exec())
