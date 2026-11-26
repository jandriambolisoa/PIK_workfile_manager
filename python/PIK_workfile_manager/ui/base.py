import os
from PySide6.QtWidgets import QMainWindow, QMessageBox

from PySide6 import QtGui, QtCore, QtWidgets
from pathlib import Path

from PIK_workfile_manager.core.base import BaseCore
from PIK_workfile_manager.core.constants import DEFAULT_FILENAME
from PIK_workfile_manager.ui.constants import OPEN_WINDOW_SIZE, LIST_FONT_SIZE, LIST_ITEMS_SIZE, SAVE_WINDOW_SIZE, MAX_SCENE_NAME_LENGTH


class _VersionPopup(QtWidgets.QListWidget):
    """
    Frameless popup list that closes on item activation, Escape, or when it
    loses focus (e.g. click outside, host application stealing focus).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        # Qt.Popup already implies a frameless top-level window.
        self.setWindowFlags(QtCore.Qt.Popup)
        self.itemClicked.connect(self.hide)
        self.itemActivated.connect(self.hide)
        self.setStyleSheet("""
            QListWidget {
                font-size: %spt;
            }
            QListWidget::item {
                height: %spx;
            }
        """ %(LIST_FONT_SIZE, LIST_ITEMS_SIZE))

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.hide()


class BaseOpenWindow(QMainWindow):

    backend: BaseCore

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowIcon(
            QtGui.QIcon(os.path.join(Path(__file__).parent, "icons", "piktura.png"))
        )
        self.setWindowTitle("Open Production Workfile")
        self.resize(*OPEN_WINDOW_SIZE)
        self.setMinimumSize(*OPEN_WINDOW_SIZE)

        # --- Widgets ---
        self.context_label = QtWidgets.QLabel()
        self.context_label.setText(self.backend._context_as_string())

        self.scene_label = QtWidgets.QLabel("Scenes :")
        self.scene_list = QtWidgets.QListWidget()
        self.scene_list.font().setPointSize(LIST_FONT_SIZE)
        self.scene_list.setMinimumHeight(LIST_ITEMS_SIZE)
        self.scene_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.file_to_open_label = QtWidgets.QLabel("File to open :")
        self.file_to_open_display = QtWidgets.QLabel("")
        self.file_to_open_display.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )
        self.file_to_open_display.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Preferred,
        )
        self.file_to_open_display.setWordWrap(True)

        self.cancel_button = QtWidgets.QPushButton("Cancel")

        self.open_button = QtWidgets.QPushButton("Open")
        self.open_button.setDefault(True)
        self.open_button.setAutoDefault(True)
        self.open_button.setFocus()

        # --- Layouts ---
        context_layout = QtWidgets.QHBoxLayout()
        context_layout.addWidget(self.context_label)

        scene_layout = QtWidgets.QHBoxLayout()
        scene_layout.addWidget(self.scene_label, alignment=QtCore.Qt.AlignTop)
        scene_layout.addWidget(self.scene_list)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.file_to_open_label)
        file_layout.addWidget(self.file_to_open_display, stretch=1)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.open_button)

        central_widget = QtWidgets.QWidget()

        self.main_layout = QtWidgets.QVBoxLayout(central_widget)
        self.main_layout.addLayout(context_layout)
        self.main_layout.addLayout(scene_layout, stretch=1)
        self.main_layout.addLayout(file_layout)
        self.main_layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

        # --- Selection Popup ---
        self.version_list = _VersionPopup(self)

        # Right-click on scene_list
        self.scene_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.scene_list.customContextMenuRequested.connect(
            self._show_version_popup
        )

        # --- Connections ---
        self.backend.workfile_open.connect(self.close)
        self.open_button.clicked.connect(self._open_workfile)
        self.open_button.clicked.connect(self.close)
        self.cancel_button.clicked.connect(self.close)
        self.scene_list.itemSelectionChanged.connect(self._populate_version_list)
        self.scene_list.itemSelectionChanged.connect(self._update_file_to_open_display)
        self.version_list.itemSelectionChanged.connect(self._update_file_to_open_display)

    def showEvent(self, event):
        super().showEvent(event)
        self.backend._refresh_scenes()
        self._populate_scene_name_list()
        self.open_button.setFocus()
        self.open_button.setDefault(True)

    def _show_version_popup(self, pos):
        item = self.scene_list.itemAt(pos)

        # Only show popup if right-clicking an item
        if item is None:
            return

        # Ensure item becomes current
        if self.scene_list.currentItem() != item:
            self.scene_list.setCurrentItem(item)
            self._populate_version_list()

        if self.version_list.count() == 0:
            return

        # Resize popup to content
        self.version_list.adjustSize()

        # Position at the global position of the right-click
        self.version_list.move(self.scene_list.viewport().mapToGlobal(pos))

        self.version_list.show()
        self.version_list.setFocus()

    def _populate_scene_name_list(self):
        self.scene_list.clear()

        scenes = list(self.backend.scenes.keys())
        if scenes:
            self.scene_list.addItems(scenes)
            self.scene_list.setCurrentRow(0)

    def _populate_version_list(self):
        self.version_list.clear()

        files = self.backend.scenes.get(self.scene_list.currentItem().text(), None)
        if files:
            files = sorted(files, reverse=True)
            self.version_list.addItems(file.name for file in files)
            self.version_list.setCurrentRow(0)

    def _update_file_to_open_display(self):
        self.file_to_open_display.clear()

        files = self.backend.scenes.get(self.scene_list.currentItem().text(), None)
        if files:
            file_to_open = files[0].parent / Path(self.version_list.currentItem().text())
            self.file_to_open_display.setText(str(file_to_open.resolve()))

    def _open_workfile(self):
        self.backend.workfile_open.emit(Path(self.file_to_open_display.text()))
        self.close()


class BaseSaveWindow(QMainWindow):

    backend: BaseCore

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowIcon(
            QtGui.QIcon(os.path.join(Path(__file__).parent, "icons", "piktura.png"))
        )
        self.setWindowTitle("Save Production Workfile")
        self.resize(*SAVE_WINDOW_SIZE)
        self.setMinimumSize(*SAVE_WINDOW_SIZE)

        # --- Widgets ---
        self.context_label = QtWidgets.QLabel()
        self.context_label.setText(self.backend._context_as_string())

        self.scene_label = QtWidgets.QLabel("Scene name :")
        self.scene_input = QtWidgets.QLineEdit()
        self.scene_input.setPlaceholderText("Enter a scene name...")
        self.scene_input.setMaxLength(MAX_SCENE_NAME_LENGTH)
        self.scene_input.setText(DEFAULT_FILENAME)

        self.version_label = QtWidgets.QLabel("Version :")
        self.version_spinbox = QtWidgets.QSpinBox()
        self.version_spinbox.setMinimum(1)
        self.version_spinbox.setMaximum(999)
        self.version_spinbox.setValue(1)
        self.version_spinbox.setDisplayIntegerBase(10)
        self.version_spinbox.setAlignment(QtCore.Qt.AlignCenter)

        self.file_to_save_label = QtWidgets.QLabel("File to save :")
        self.file_to_save_display = QtWidgets.QLabel("")
        self.file_to_save_display.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )
        self.file_to_save_display.setWordWrap(True)

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.setDefault(True)
        self.save_button.setAutoDefault(True)
        self.save_button.setFocus()

        # --- Layouts ---
        context_layout = QtWidgets.QHBoxLayout()
        context_layout.addWidget(self.context_label)

        scene_layout = QtWidgets.QHBoxLayout()
        scene_layout.addWidget(self.scene_label, alignment=QtCore.Qt.AlignTop)
        scene_layout.addWidget(self.scene_input)

        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.version_label)
        version_layout.addWidget(self.version_spinbox, stretch=1)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.file_to_save_label)
        file_layout.addWidget(self.file_to_save_display, stretch=1)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.addLayout(context_layout)
        main_layout.addLayout(scene_layout)
        main_layout.addLayout(version_layout)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

        # --- Connections ---
        self.backend.workfile_save.connect(self.close)
        self.scene_input.textChanged.connect(self._update_version_spinbox)
        self.version_spinbox.valueChanged.connect(self._update_file_to_save_display)
        self.cancel_button.clicked.connect(self.close)
        self.save_button.clicked.connect(self._save_workfile)


    def showEvent(self, event):
        super().showEvent(event)
        self.backend._refresh_scenes()
        self._update_version_spinbox()
        self._update_file_to_save_display()
        self.save_button.setFocus()
        self.save_button.setDefault(True)

    def _update_version_spinbox(self):
        filepath = self.backend._next_version(self.scene_input.text())
        print("# DEBUG - %s"%filepath)
        version_value = self.backend._get_scene_version_value(filepath)
        print("# DEBUG - %s"%version_value)
        self.version_spinbox.setValue(version_value)

    def _update_file_to_save_display(self):
        self.file_to_save_display.clear()
        filepath = self.backend.generate_save_workfile_filepath(
            self.scene_input.text(),
            self.version_spinbox.value()
        )
        self.file_to_save_display.setText(str(filepath))

    def _save_workfile(self):
        file_to_save = Path(self.file_to_save_display.text())

        if file_to_save.exists():
            button = QMessageBox.question(
                self,
                "File already exists",
                f"File already exists: {file_to_save.name}. Do you want to overwrite it?",
            )
            if button == QMessageBox.No:
                return

        self.backend.workfile_save.emit(Path(self.file_to_save_display.text()), True)

        self.close()
