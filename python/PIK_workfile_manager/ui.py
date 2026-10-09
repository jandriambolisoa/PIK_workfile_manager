import os
from PySide6 import QtCore, QtWidgets, QtGui
from pathlib import Path

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
    DEFAULT_FILENAME,
    MAX_ENTITY_DISPLAY,
    MAX_SCENE_NAME_LENGTH,
)
from PIK_workfile_manager.core import QABCMeta, find_closest_strings


class FileOpenWindow(QtWidgets.QWidget, metaclass=QABCMeta):
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

        if not isinstance(self.context, Asset) or not isinstance(self.context, Shot):
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
        self.entity_label = QtWidgets.QLabel("Entity :")
        self.entity_combobox = QtWidgets.QComboBox()
        self.entity_combobox.setMaxVisibleItems(MAX_ENTITY_DISPLAY)

        self.scene_label = QtWidgets.QLabel("Scenes :")
        self.scene_list = QtWidgets.QListWidget()
        self.scene_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.version_label = QtWidgets.QLabel("Versions :")
        self.version_list = QtWidgets.QListWidget()
        self.version_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.file_to_open_label = QtWidgets.QLabel("File to open :")
        self.file_to_open_display = QtWidgets.QLabel("")
        self.file_to_open_display.setTextInteractionFlags(
            QtCore.Qt.TextSelectableByMouse
        )

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.open_button = QtWidgets.QPushButton("Open")
        self.open_button.setDefault(True)

        # --- Layouts ---
        entity_layout = QtWidgets.QHBoxLayout()
        entity_layout.addWidget(self.entity_label)
        entity_layout.addWidget(self.entity_combobox)

        scene_layout = QtWidgets.QHBoxLayout()
        scene_layout.addWidget(self.scene_label, alignment=QtCore.Qt.AlignTop)
        scene_layout.addWidget(self.scene_list)

        version_layout = QtWidgets.QHBoxLayout()
        version_layout.addWidget(self.version_label, alignment=QtCore.Qt.AlignTop)
        version_layout.addWidget(self.version_list)

        file_layout = QtWidgets.QHBoxLayout()
        file_layout.addWidget(self.file_to_open_label)
        file_layout.addWidget(self.file_to_open_display)
        file_layout.addStretch()

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.open_button)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(entity_layout)
        main_layout.addLayout(scene_layout)
        main_layout.addLayout(version_layout)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(button_layout)

        # --- Connections ---
        self.entity_combobox.currentIndexChanged.connect(self._populate_scene_name_list)
        self.entity_combobox.currentIndexChanged.connect(self._populate_version_list)
        self.entity_combobox.currentIndexChanged.connect(
            self._update_file_to_open_display
        )
        self.scene_list.itemSelectionChanged.connect(self._populate_version_list)
        self.scene_list.itemSelectionChanged.connect(self._update_file_to_open_display)
        self.version_list.itemSelectionChanged.connect(
            self._update_file_to_open_display
        )
        self.open_button.clicked.connect(self.open_workfile)
        self.cancel_button.clicked.connect(self.close_window)

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
                project=self.context.project, category=self.context.asset_type
            )
            items_to_add = find_closest_strings(
                self.context.name,
                [asset.name for asset in tmp_context.assets],
            )
            self.entity_combobox.addItems(items_to_add)
            return

        if isinstance(self.context, Shot):
            tmp_context = get_context(
                project=self.context.project, category=self.context.sequence
            )
            items_to_add = find_closest_strings(
                self.context.name,
                [shot.name for shot in tmp_context.shots],
            )
            self.entity_combobox.addItems(items_to_add)
            return

    def _populate_scene_name_list(self):
        """
        Populate the scene list with scene names available for the selected entity.

        Scene names are collected from existing workfiles matching the current
        project, entity, step, software, and file extension.
        """
        self.scene_list.clear()

        if isinstance(self.context, Asset):
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "asset_type": self.context.asset_type,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v000",
                }
            ).from_data()

        else:
            # Shot context
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "sequence": self.context.sequence,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v000",
                }
            ).from_data()

        existing_scene_files = [
            ProductionPath(file) for file in filepath.parent.glob(f"*.{self.extension}")
        ]
        existing_scene_names = set()

        for file in existing_scene_files:
            datas = file.as_data()
            existing_scene_names.add(datas["scene_name"])

        if existing_scene_names:
            self.scene_list.addItems(list(existing_scene_names))

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
        selected_scene_name = selected_items[0].text()

        # Get all available versions for the selected scene name
        if isinstance(self.context, Asset):
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "asset_type": self.context.asset_type,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": selected_scene_name,
                    "version": "v*",
                }
            ).from_data()

        else:
            # Shot context
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "sequence": self.context.sequence,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": selected_scene_name,
                    "version": "v*",
                }
            ).from_data()

        versions = sorted(filepath.parent.glob(filepath.name), reverse=True)

        if not versions:
            return

        versions[0] = f"(latest) {versions[0]}"

        # Populate the version list widget with the available versions
        self.version_list.addItems(versions)

    @QtCore.Slot()
    def _update_file_to_open_display(self):
        """
        Update the displayed workfile path from the current UI selections.

        The path is built from the selected entity and version within the current
        production context.
        """
        self.file_to_open_display.clear()

        if isinstance(self.context, Asset):
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "asset_type": self.context.asset_type,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v000",
                }
            ).from_data()

        else:
            # Shot context
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "sequence": self.context.sequence,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v000",
                }
            ).from_data()

        filepath = filepath.parent / self.version_list.currentItem().text()
        self.file_to_open_display.setText(filepath.as_posix())

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


class FileSaveWindow(QtWidgets.QWidget, metaclass=QABCMeta):
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

        if not isinstance(self.context, Asset) or not isinstance(self.context, Shot):
            raise RuntimeError(
                "Save file is not supported in this context. Must be an Asset or a Shot context."
            )

        if not self.context.step:
            raise RuntimeError(
                "Save file is not supported in this context. A step is required."
            )

        self.setWindowTitle("Save Production Workfile")
        self.resize(*OPEN_WINDOW_SIZE)
        self.setMinimumSize(*OPEN_WINDOW_SIZE)
        self.setWindowIcon(
            QtGui.QIcon(os.path.join(Path(__file__).parent, "icons", "piktura.png"))
        )

        # --- Widgets ---
        self.entity_label = QtWidgets.QLabel("Entity :")
        self.entity_combobox = QtWidgets.QComboBox()
        self.entity_combobox.setMaxVisibleItems(MAX_ENTITY_DISPLAY)

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

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(entity_layout)
        main_layout.addLayout(scene_layout)
        main_layout.addLayout(version_layout)
        main_layout.addLayout(file_layout)
        main_layout.addLayout(button_layout)

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
                project=self.context.project, category=self.context.asset_type
            )
            items_to_add = find_closest_strings(
                self.context.name,
                [asset.name for asset in tmp_context.assets],
            )
            self.entity_combobox.addItems(items_to_add)
            return

        if isinstance(self.context, Shot):
            tmp_context = get_context(
                project=self.context.project, category=self.context.sequence
            )
            items_to_add = find_closest_strings(
                self.context.name,
                [shot.name for shot in tmp_context.shots],
            )
            self.entity_combobox.addItems(items_to_add)
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
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "asset_type": self.context.asset_type,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": "v*",
                }
            ).from_data()

        else:
            # Shot context
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "sequence": self.context.sequence,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": "v*",
                }
            ).from_data()

        versions = sorted(filepath.parent.glob(filepath.name), reverse=True)

        if not versions:
            self.version_spinbox.setValue(1)
            return

        self.version_spinbox.setValue(int(versions[0][1:]) + 1)

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
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "asset_type": self.context.asset_type,
                    "asset_name": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": f"v{self.version_spinbox.value():03d}",
                }
            ).from_data()

        else:
            # Shot context
            filepath = ProductionPath(
                {
                    "project": self.context.project,
                    "sequence": self.context.sequence,
                    "shot": self.entity_combobox.currentText(),
                    "step": self.context.step,
                    "software": self.software,
                    "extension": self.extension,
                    "scene_name": self.scene_input.text(),
                    "version": f"v{self.version_spinbox.value():03d}",
                }
            ).from_data()

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
