import subprocess
import sys
import logging
from urllib.parse import unquote
import platform
import os.path

from PySide6 import QtCore, QtWidgets, QtGui

logger = logging.getLogger(__name__)

MIME_WIN_IDLIST = 'application/x-qt-windows-mime;value="Shell IDList Array"'
MIME_WIN_FILENAMEW = 'application/x-qt-windows-mime;value="FileNameW"'
MIME_URI_LIST = "text/uri-list"

APP_NAME = "File manager"

OS = platform.system()
is_windows = (OS == "Windows")

DROP_ACTIONS = (QtCore.Qt.CopyAction, QtCore.Qt.MoveAction, QtCore.Qt.LinkAction, QtCore.Qt.ActionMask, QtCore.Qt.IgnoreAction,
	QtCore.Qt.TargetMoveAction)

def get_paths_from_drop_event(event):

	mimedata = event.mimeData().data(MIME_URI_LIST).data()

	schema = "file:///"
	files = []
	for uri in mimedata.split(b"\r\n")[:-1]:
		tmp = unquote(uri.decode("ascii"))
		if tmp.startswith(schema):
			tmp = tmp[len(schema):]
			if not os.path.exists(tmp):
				raise FileNotExistsError(tmp)
			files.append(tmp)

	return files

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

def dropactionsstr(dropactions):
	res = []
	for action in DROP_ACTIONS:
		if action & dropactions:
			res.append(str(action))

	return ", ".join(res)

class FileManagerView(QtWidgets.QTableView):

	middle_clicked = QtCore.Signal(QtCore.QModelIndex)

	def __init__(self, parent):
		super().__init__(parent)
		self.setSortingEnabled(True)
		self.setShowGrid(False)
		self.verticalHeader().setVisible(False)
		self.setAcceptDrops(True)
		self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
		self.setDragEnabled(True)
		self.setDropIndicatorShown(True)
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

	def root_dir(self) -> str:
		return self.model().filePath(self.rootIndex())

	def samedrivedrop(self, event: QtGui.QDropEvent) -> bool:
		if is_windows:
			files = get_paths_from_drop_event(event)
			drive_a = os.path.splitdrive(os.path.commonprefix(files))[0]
			drive_b = os.path.splitdrive(self.root_dir())[0]

			res = drive_a.lower() == drive_b.lower()

			return res
		else:
			return False

	def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
		print("dragEnterEvent", event)

		formats = event.mimeData().formats()

		if MIME_URI_LIST in formats:
			self.setBackgroundRole(QtGui.QPalette.Highlight) ## fixme

			mods = event.keyboardModifiers()
			ctrl = QtCore.Qt.ControlModifier
			shift = QtCore.Qt.ShiftModifier

			# this is not saved for future QDropEvent
			if mods & shift and mods & ctrl:
				event.setDropAction(QtCore.Qt.LinkAction)
			elif mods & shift:
				event.setDropAction(QtCore.Qt.MoveAction)
			elif mods & ctrl:
				event.setDropAction(QtCore.Qt.CopyAction)
			elif self.samedrivedrop(event):
				event.setDropAction(QtCore.Qt.MoveAction)
			else:
				event.setDropAction(QtCore.Qt.CopyAction)

			event.accept()
			#emit changed(event->mimeData());
		else:
			print(formats)
			print(dropactionsstr(event.possibleActions()))

	def dragMoveEvent(self, event: QtGui.QDragMoveEvent):
		event.accept()

	def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent):
		print("dragLeaveEvent", event)

	def dropEvent(self, event: QtGui.QDropEvent):

		formats = event.mimeData().formats()

		if MIME_URI_LIST in formats:
			files = get_paths_from_drop_event(event)
			action = event.dropAction()
			target = self.root_dir()
			if event.source(): # internal drag and drop
				print(action, files, "to", target)
			else: # external drag and drop
				print(action, files, "to", target)
			event.accept()
		else:
			for format in formats:
				print(format, event.mimeData().data(format))

	@QtCore.Slot()
	def handle_middle_clicked(self, event: QtCore.QModelIndex):
		wm.create(MyWidget(event.model(), event))

	@QtCore.Slot()
	def handle_action_open(self, event):
		print("handle_action_open", event)

	@QtCore.Slot()
	def handle_action_open_new(self, event):
		print("handle_action_open_new", event)
		wm.create(MyWidget())

	@QtCore.Slot()
	def handle_action_open_default(self, event):
		print("handle_action_open_default", event)

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
	def __init__(self, model, index=None, parent=None):
		super().__init__(parent)

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
		print("handle_action_back", event)

class MyTray(QtWidgets.QSystemTrayIcon):

	def __init__(self, app, wm, parent=None):
		QtWidgets.QSystemTrayIcon.__init__(self, parent)

		self.app = app
		self.wm = wm

		self.setIcon(app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
		self.setToolTip(APP_NAME)

		menu = QtWidgets.QMenu()
		action_open = QtGui.QAction("Open", self)
		action_close_windows = QtGui.QAction("Close windows", self)
		action_close = QtGui.QAction("Close", self)

		action_open.triggered.connect(self.handle_action_open)
		action_close_windows.triggered.connect(self.handle_action_close_windows)
		action_close.triggered.connect(self.handle_action_close)

		menu.addAction(action_open)
		menu.addAction(action_close_windows)
		menu.addAction(action_close)

		self.setContextMenu(menu)

	@QtCore.Slot()
	def handle_action_open(self, event):
		root = QtCore.QDir.currentPath()
		logger.warning("Current path: %s", root)

		self.wm.create(MyWidget(get_model_b(root)))

	@QtCore.Slot()
	def handle_action_close_windows(self, event):
		self.app.closeAllWindows()

	@QtCore.Slot()
	def handle_action_close(self, event):
		self.app.quit()

class WindowManager:

	def __init__(self):
		self.widgets = []

	def create(self, widget):
		self.widgets.append(widget)
		widget.show()

if __name__ == "__main__":
	app = QtWidgets.QApplication([])
	app.setQuitOnLastWindowClosed(False) # systray is not a window

	wm = WindowManager()
	wm.create(MyTray(app, wm))

	root = QtCore.QDir.currentPath()
	logger.warning("Current path: %s", root)

	wm.create(MyWidget(get_model_b(root)))

	sys.exit(app.exec())
