from pathlib import Path

from maya import cmds, OpenMaya, OpenMayaUI

from PIK_workfile_manager.core.base import BaseCore


class MayaCore(BaseCore):

    def __init__(self):
        super().__init__("maya", "ma")

    def open_workfile(self, filepath: Path):
        filepath = super().open_workfile(filepath)
        cmds.file(filepath.resolve(), open=True)
        OpenMaya.MGlobal.displayInfo(f"Opened {filepath}")

    def save_workfile(self, filepath: Path):
        filepath = super().save_workfile(filepath)
        cmds.file(rename=filepath)
        cmds.file(save=True, force=True)
        OpenMaya.MGlobal.displayInfo(f"Saved {filepath}")


