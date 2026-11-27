import os
from pathlib import Path

import hou

from PIK_workfile_manager.core.base import BaseCore

HOUDINI_PROJECT_FOLDERS = (
    "geo",
    "hda",
    "sim",
    "abc",
    "tex",
    "render",
    "flip",
    "scripts",
    "comp",
    "audio",
    "video",
    "desk"
)

class HoudiniCore(BaseCore):

    def __init__(self):
        super().__init__("houdini", "hip")

    @staticmethod
    def get_houdini_project_root(path: Path) -> Path:
        """Get the "houdini" folder used as a houdini project root.

        Returns:
            Path: houdini project root.
        """
        houdini_project_path = path.parent
        while houdini_project_path.name != "houdini":
            houdini_project_path = houdini_project_path.parent

        return houdini_project_path


    def open_workfile(self, filepath: Path):
        """Open a hip file from disk.

        Arguments:
            filepath (Path): Path where the file must be saved.
        """
        filepath = super().open_workfile(filepath)

        # See for more details: https://www.sidefx.com/docs/houdini/basics/project.html
        os.environ["JOB"] = HoudiniCore.get_houdini_project_root(filepath).resolve().as_posix()

        try:
            hou.hipFile.load(filepath.resolve().as_posix(), ignore_load_warnings=True)
        except hou.OperationFailed:
            print("Opening file failed")
            return


    def save_workfile(self, filepath: Path):
        """Save the hip file to disk.

        Note: The file saved is not added to recent files to avoid student loading files from the recent menu.

        Arguments:
            filepath (Path): Path where the file must be saved.
        """
        filepath = super().save_workfile(filepath)

        project_root = HoudiniCore.get_houdini_project_root(filepath).resolve()

        # See for more details: https://www.sidefx.com/docs/houdini/basics/project.html
        for folder in HOUDINI_PROJECT_FOLDERS:
            os.makedirs(project_root / folder)

        try:
            hou.hipFile.save(filepath, save_to_recent_files=False)
        except hou.OperationFailed:
            print("Saving file failed")
            return

        os.environ["JOB"] = project_root.as_posix()
