from PySide6.QtWidgets import QWidget
from shiboken6 import wrapInstance

from maya import cmds, OpenMaya, OpenMayaUI

from PIK_workfile_manager.ui import FileOpenWindow, FileSaveWindow


def get_maya_main_window():
    """
    Get the maya main window object.
    Returns:
        class: `QWidget`: The maya main window object.
    """
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)


class MayaFileOpenWindow(FileOpenWindow):
    def __init__(self):
        super().__init__(parent=get_maya_main_window(), software="maya", extension="ma")

    def open_workfile(self):
        filepath = super().open_workfile()
        cmds.file(filepath, open=True)
        OpenMaya.MGlobal.displayInfo(f"Opened {filepath}")

    def close_window(self):
        OpenMaya.MGlobal.displayInfo("Closing workfile manager.")
        super().close_window()


class MayaFileSaveWindow(FileSaveWindow):
    def __init__(self):
        super().__init__(parent=get_maya_main_window(), software="maya", extension="ma")

    def save_workfile(self):
        filepath = super().save_workfile()
        cmds.file(rename=filepath)
        cmds.file(save=True, force=True)
        OpenMaya.MGlobal.displayInfo(f"Saved {filepath}")

    def close_window(self):
        OpenMaya.MGlobal.displayInfo("Closing workfile manager.")
        super().close_window()
