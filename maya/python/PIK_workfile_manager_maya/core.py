from PySide6.QtWidgets import QWidget
from pathlib import Path
from shiboken6 import wrapInstance

from maya import cmds, OpenMaya, OpenMayaUI

from PIK_workfile_manager.core.base import BaseCore

class MayaCore(BaseCore):
    """
    Maya-specific implementation of the workfile manager.

    Provides workfile opening and saving operations using Maya commands,
    including workspace management and initialization.
    """

    def __init__(self):
        """
        Initialize the Maya workfile manager.

        Configures the backend to manage Maya ASCII workfiles (.ma).
        """
        super().__init__("maya", "ma")

    def open_workfile(self, filepath: Path):
        """
        Open a Maya workfile and set the corresponding workspace.

        Validates the filepath, switches the active Maya workspace,
        and opens the requested scene.

        Args:
            filepath: Workfile path to open.
        """
        filepath = super().open_workfile(filepath)

        # Set the maya workspace
        workspace_folder_path = filepath.parent.parent
        cmds.workspace(workspace_folder_path.resolve(), openWorkspace=True)

        cmds.file(filepath.resolve(), open=True)
        OpenMaya.MGlobal.displayInfo(f"Opened {filepath}")

    def save_workfile(self, filepath: Path):
        """
        Save the current Maya scene as a production workfile.

        Ensures the target workspace exists and is active,
        then renames and saves the current scene.

        Args:
            filepath: Destination workfile path.
        """
        filepath = super().save_workfile(filepath)

        # Set the maya workspace
        workspace_folder_path = filepath.parent.parent
        if Path(cmds.workspace(q=True, directory=True)).resolve() != workspace_folder_path.resolve():
            try:
                cmds.workspace(workspace_folder_path.resolve(), newWorkspace=True)
                cmds.workspace(workspace_folder_path.resolve(), saveWorkspace=True)
                self._create_workspace_folders(workspace_folder_path)
            except RuntimeError:
                cmds.workspace(workspace_folder_path.resolve(), openWorkspace=True)

        cmds.file(rename=filepath)
        cmds.file(save=True, force=True)
        OpenMaya.MGlobal.displayInfo(f"Saved {filepath}")

    def _create_workspace_folders(self, workspace_folder_path: Path):
        """
        Create the standard Maya workspace directory structure.

        Directories are created from the current Maya workspace
        file rules if they do not already exist.

        Args:
            workspace_folder_path: Root workspace directory.
        """
        for file_rule in cmds.workspace(query=True, fileRuleList=True):
            to_create = workspace_folder_path / Path(cmds.workspace(fileRuleEntry=file_rule))
            to_create.mkdir(parents=True, exist_ok=True)


def get_maya_main_window():
    """
    Return the Maya main window as a Qt widget.

    This utility is used to parent custom Qt windows
    to the Maya application window.

    Returns:
        QWidget: Maya's main window.
    """
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)