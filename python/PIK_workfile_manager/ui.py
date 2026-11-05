import os
import platform
from PySide6 import QtCore, QtWidgets, QtGui
from pathlib import Path

from abc import abstractmethod
from rez_production_context.contexts import (
    Studio,
    Project,
    AssetType,
    Asset,
    Sequence,
    Shot,
)
from rez_production_context import get_context, get_context_from_env

from PIK_path_manager import ProductionPath

from PIK_workfile_manager.constants import (
    OPEN_WINDOW_SIZE,
    SAVE_WINDOW_SIZE,
    DEFAULT_FILENAME,
    MAX_SCENE_NAME_LENGTH,
    LIST_FONT_SIZE,
    LIST_ITEMS_SIZE,
)
from PIK_workfile_manager.core import QABCMeta, get_existing_scene_names, get_existing_scene_versions


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


class FileOpenWindow(QtWidgets.QMainWindow, metaclass=QABCMeta):
    """
    Base window for browsing and opening production workfiles.

    The available entities, scenes, and versions are derived from the current
    production context. Only Asset and Shot contexts with a valid step are
    supported.

    Subclasses must implement the workfile opening and window closing behavior.
    """

    def __init__(self, parent=None, software=None, extension=None):
        """
        Initialize the production workfile browser.

        Args:
            parent: Optional parent Qt widget.
            software: Software identifier used to resolve production paths.
            extension: Workfile extension, with or without a leading dot.

        Raises:
            RuntimeError: If the current context is not an Asset or Shot, or if no
                production step is defined.
        """
        super().__init__(parent)
        self.context = get_context_from_env()
        self.software = software
        self.extension = extension.lower().lstrip(".")

        self.root = ProductionPath._canonical_roots["/L33D/"][platform.system().lower()]
        # self.root = "//SRV-W25-FIL-03/L33D/"

        if not isinstance(self.context, Asset) and not isinstance(self.context, Shot):
            raise RuntimeError(
                "Open file is not supported in this context. Must be an Asset or a Shot context."
            )

        if not self.context.step:
            raise RuntimeError(
                "Open file is not supported in this context. A step is required."
            )

        self.setWindowTitle("Open Production Workfile")
        self.resize(*OPEN_WINDOW_SIZE)
        self.setMinimumSize(*OPEN_WINDOW_SIZE)
        self.setWindowIcon(
            QtGui.QIcon(os.path.join(Path(__file__).parent, "icons", "piktura.png"))
        )

        # --- Widgets ---
        if isinstance(self.context, Asset):
            self.context_label = QtWidgets.QLabel(
                f"Project: {self.context.project.name} | Asset type: {self.context.asset_type.name} | Asset: {self.context.name} | Step: {self.context.step}"
            )
        else:
            self.context_label = QtWidgets.QLabel(
                f"Project: {self.context.project.name} | Sequence: {self.context.sequence.name} | Shot: {self.context.name} | Step: {self.context.step}"
            )

        self.scene_label = QtWidgets.QLabel("Scenes :")
        self.scene_list = QtWidgets.QListWidget()
        self.scene_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.scene_list.setStyleSheet("""
            QListWidget {
                font-size: %spt;
            }
            QListWidget::item {
                height: %spx;
            }
        """ %(LIST_FONT_SIZE, LIST_ITEMS_SIZE))

        self.file_to_open_label = QtWidgets.QLabel("File to open :")
        self.file_to_open_display = QtWidgets.QLabel("")
        self.file_to_open_display.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
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
        file_layout.addStretch()

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.open_button)

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.addLayout(context_layout)
        main_layout.addLayout(scene_layout)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

        # --- Selection Popup ---
        self.version_list = _VersionPopup(self)

        # --- Connections ---
        self.scene_list.itemSelectionChanged.connect(self._populate_version_list)
        self.scene_list.itemSelectionChanged.connect(self._update_file_to_open_display)
        self.scene_list.itemSelectionChanged.connect(self._refocus_open_button)
        self.version_list.itemSelectionChanged.connect(
            self._update_file_to_open_display
        )
        self.version_list.itemSelectionChanged.connect(
            self._display_if_selected_version_is_latest
        )
        self.version_list.itemSelectionChanged.connect(self._refocus_open_button)
        self.open_button.clicked.connect(self.open_workfile)
        self.cancel_button.clicked.connect(self.close_window)

        # Right-click on scene_list
        self.scene_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.scene_list.customContextMenuRequested.connect(
            self._show_version_popup
        )

        # Initiate the UI datas
        self._populate_scene_name_list()


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
        """
        Populate the scene list with scene names available for the selected entity.

        Scene names are collected from existing workfiles matching the current
        project, entity, step, software, and file extension.
        """
        self.scene_list.clear()

        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v000",
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v000",
                }
            )

        scene_names = get_existing_scene_names(filepath.parent, self.extension)

        if scene_names:
            self.scene_list.addItems(scene_names)
            self.scene_list.setCurrentRow(0)

    @QtCore.Slot()
    def _populate_version_list(self):
        """
        Populate the version list for the currently selected scene.

        Available workfile versions are sorted in descending order, with the most
        recent version marked as latest. The list remains empty when no scene is
        selected or no versions are found.
        """
        self.version_list.clear()

        # Get the selected scene name from the scene list widget
        selected_items = self.scene_list.selectedItems()
        if not selected_items:
            return
        selected_scene_name = selected_items[0].text().removesuffix(" (latest)")

        # Get all available versions for the selected scene name
        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": selected_scene_name,
                    "version": "v*",
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": selected_scene_name,
                    "version": "v*",
                }
            )

        versions = get_existing_scene_versions(filepath.parent, selected_scene_name, self.extension)
        print("# DEBUG - %s"%selected_scene_name)
        print("# DEBUG - %s"%versions)
        print("# DEBUG - %s"%filepath.parent)

        if not versions:
            return

        versions = sorted(versions, reverse=True)

        # Populate the version list widget with the available versions
        self.version_list.addItems(versions)
        self.version_list.setCurrentRow(0)

    @QtCore.Slot()
    def _update_file_to_open_display(self):
        """
        Update the displayed workfile path from the current UI selections.

        The path is built from the selected entity and version within the current
        production context.
        """
        self.file_to_open_display.clear()

        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": self.scene_list.currentItem().text().removesuffix(" (latest)"),
                    "version": self.version_list.currentItem().text(),
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": self.scene_list.currentItem().text().removesuffix(" (latest)"),
                    "version": self.version_list.currentItem().text(),
                }
            )

        if filepath.exists():
            self.file_to_open_display.setText(filepath.as_posix())

    def _display_if_selected_version_is_latest(self):
        scene_item = self.scene_list.currentItem()
        scene_item_text = scene_item.text()
        scene_item.setText(scene_item_text.removesuffix(" (latest)"))

        if self.version_list.currentRow() == 0:
            scene_item.setText(scene_item.text() + " (latest)")
        else:
            scene_item.setText(scene_item.text().removesuffix(" (latest)"))

    def _refocus_open_button(self):
        self.open_button.setFocus()

    def showEvent(self, event):
        super().showEvent(event)

        self.open_button.setDefault(True)
        self.open_button.setFocus()

    @QtCore.Slot()
    @abstractmethod
    def open_workfile(self):
        """
        Return the path of the workfile selected for opening.

        Subclasses should extend this method to perform the software-specific
        workfile opening operation.

        Returns:
            str: Path currently displayed as the workfile to open.
        """
        return self.file_to_open_display.text()

    @QtCore.Slot()
    @abstractmethod
    def close_window(self):
        """
        Close the workfile browser window.

        Subclasses may extend this method to perform software-specific cleanup before
        closing the window.
        """
        self.close()


class FileSaveWindow(QtWidgets.QMainWindow, metaclass=QABCMeta):
    """
    Base window for creating and saving production workfiles.

    This widget provides a generic user interface for workfile creation in an
    Asset or Shot context. The user selects a target entity, enters a scene name,
    chooses a version number, and reviews the generated filepath before saving.

    Subclasses must implement the software-specific save logic by overriding
    `save_workfile()`. They may also customize the window closing behavior by
    overriding `close_window()`.

    Args:
        parent: Optional parent widget.
        software: Name of the target DCC software.
        extension: Workfile extension, with or without a leading dot.

    Raises:
        RuntimeError: If the current context is not an Asset or Shot.
        RuntimeError: If the current context has no associated step.
    """

    def __init__(self, parent=None, software=None, extension=None):
        super().__init__(parent)
        self.context = get_context_from_env()
        self.software = software
        self.extension = extension.lower().lstrip(".")

        self.root = ProductionPath._canonical_roots["/L33D/"][platform.system().lower()]

        if not isinstance(self.context, Asset) and not isinstance(self.context, Shot):
            raise RuntimeError(
                "Save file is not supported in this context. Must be an Asset or a Shot context."
            )

        if not self.context.step:
            raise RuntimeError(
                "Save file is not supported in this context. A step is required."
            )

        self.setWindowTitle("Save Production Workfile")
        self.resize(*SAVE_WINDOW_SIZE)
        self.setMinimumSize(*SAVE_WINDOW_SIZE)
        self.setWindowIcon(
            QtGui.QIcon(os.path.join(Path(__file__).parent, "icons", "piktura.png"))
        )

        # --- Widgets ---
        self.entity_label = QtWidgets.QLabel("Entity :")
        self.entity_combobox = QtWidgets.QComboBox()

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

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.setDefault(True)

        # --- Layouts ---
        entity_layout = QtWidgets.QHBoxLayout()
        entity_layout.addWidget(self.entity_label)
        entity_layout.addWidget(self.entity_combobox)

        scene_layout = QtWidgets.QHBoxLayout()
        scene_layout.addWidget(self.scene_label, alignment=QtCore.Qt.AlignTop)
        scene_layout.addWidget(self.scene_input)

        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.version_label)
        version_layout.addWidget(self.version_spinbox)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.file_to_save_label)
        file_layout.addWidget(self.file_to_save_display)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)

        central_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.addLayout(entity_layout)
        main_layout.addLayout(scene_layout)
        main_layout.addLayout(version_layout)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(button_layout)

        self.setCentralWidget(central_widget)

        # --- Connections ---
        self.entity_combobox.currentIndexChanged.connect(self._update_version_spinbox)
        self.entity_combobox.currentIndexChanged.connect(
            self._update_file_to_save_display
        )

        self.scene_input.textChanged.connect(self._update_version_spinbox)
        self.scene_input.textChanged.connect(self._update_file_to_save_display)

        self.version_spinbox.valueChanged.connect(self._update_file_to_save_display)

        self.cancel_button.clicked.connect(self.close_window)
        self.save_button.clicked.connect(self.save_workfile)

        # Initiate the UI datas
        self._populate_entity_list()

    def _populate_entity_list(self):
        """
        Populate the entity combobox with entities related to the current context.
        The closest matches to the current entity are placed first.
        """
        self.entity_combobox.clear()

        if isinstance(self.context, Asset):
            tmp_context = get_context(
                project=self.context.project.name, category=self.context.asset_type.name
            )
            # items_to_add = find_closest_strings(
            #     self.context.name,
            #     [asset.name for asset in tmp_context.assets],
            # )
            # self.entity_combobox.addItems(items_to_add)
            return

        if isinstance(self.context, Shot):
            tmp_context = get_context(
                project=self.context.project.name, category=self.context.sequence.name
            )
            # items_to_add = find_closest_strings(
            #     self.context.name,
            #     [shot.name for shot in tmp_context.shots],
            # )
            # self.entity_combobox.addItems(items_to_add)
            return

    def _update_version_spinbox(self):
        """
        Update the version spinbox with the next available version number for the
        currently selected entity and scene name.

        The workfile directory is scanned for matching workfiles and the spinbox is
        set to the highest existing version plus one. If no matching workfiles are
        found, the version is reset to 1.
        """
        # Get all available versions for the selected scene name
        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": "v*",
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": "v*",
                }
            )

        versions = sorted(filepath.parent.glob(filepath.name), reverse=True)

        if not versions:
            self.version_spinbox.setValue(1)
            return

        versions = [Path(version.name).stem.split("_")[-1].lstrip("v") for version in versions]
        self.version_spinbox.setValue(int(versions[0]) + 1)

    @QtCore.Slot()
    def _update_file_to_save_display(self):
        """
        Update the displayed filepath preview based on the current entity selection,
        scene name, version number, software, and extension.

        The generated filepath is displayed in the file preview label and represents
        the exact location where the workfile will be saved.
        """
        self.file_to_save_display.clear()

        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": f"v{self.version_spinbox.value():03d}",
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "mount": self.root,
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": f"v{self.version_spinbox.value():03d}",
                }
            )

        self.file_to_save_display.setText(filepath.as_posix())

    @QtCore.Slot()
    @abstractmethod
    def save_workfile(self):
        """
        Prepare the filepath for saving a new production workfile.

        This base implementation validates that the target workfile does not already
        exist, creates the required parent directories, and returns the resolved
        filepath. Subclasses should call this method before performing any
        software-specific save operation.

        Raises:
            FileExistsError: If a workfile already exists at the target filepath.

        Returns:
            str: Full filepath where the workfile should be saved.
        """
        to_save = Path(self.file_to_save_display.text())

        if to_save.exists():
            raise FileExistsError(f"File already exists: {to_save}")

        to_save.mkdir(parents=True, exist_ok=True)

        return to_save.as_posix()

    @QtCore.Slot()
    @abstractmethod
    def close_window(self):
        """
        Close the save workfile window.

        Subclasses may extend this method to perform software-specific cleanup before
        closing the window.
        """
        self.close()
