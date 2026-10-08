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

from python.PIK_workfile_manager.constants import (
    OPEN_WINDOW_SIZE,
    DEFAULT_FILENAME,
    MAX_ENTITY_DISPLAY,
)
from python.PIK_workfile_manager.core import QABCMeta, find_closest_strings


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
        self.entity_combobox.currentIndexChanged.connect(self.populate_scene_name_list)
        self.entity_combobox.currentIndexChanged.connect(self.populate_version_list)
        self.entity_combobox.currentIndexChanged.connect(
            self.update_file_to_open_display
        )
        self.scene_list.itemSelectionChanged.connect(self.populate_version_list)
        self.scene_list.itemSelectionChanged.connect(self.update_file_to_open_display)
        self.version_list.itemSelectionChanged.connect(self.update_file_to_open_display)
        self.open_button.clicked.connect(self.open_workfile)
        self.cancel_button.clicked.connect(self.close_window)

        # Initiate the UI datas
        self.populate_entity_list()

    def populate_entity_list(self):
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

    def populate_scene_name_list(self):
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
    def populate_version_list(self):
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
    def update_file_to_open_display(self):
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
