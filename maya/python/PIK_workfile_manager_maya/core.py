from pathlib import Path

from maya import cmds, OpenMaya, OpenMayaUI

from PIK_workfile_manager.core.base import BaseCore


class MayaCore(BaseCore):

    def __init__(self):
        super().__init__("maya", "ma")

    def open_workfile(self, filepath: Path):
        filepath = super().open_workfile(filepath)

        # Set the maya workspace
        workspace_folder_path = filepath.parent.parent
        cmds.workspace(workspace_folder_path.resolve(), openWorkspace=True)

        cmds.file(filepath.resolve(), open=True)
        OpenMaya.MGlobal.displayInfo(f"Opened {filepath}")

    def save_workfile(self, filepath: Path):
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
        for file_rule in cmds.workspace(query=True, fileRuleList=True):
            to_create = workspace_folder_path / Path(cmds.workspace(fileRuleEntry=file_rule))
            to_create.mkdir(parents=True, exist_ok=True)


