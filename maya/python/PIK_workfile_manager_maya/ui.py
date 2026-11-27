from PySide6.QtWidgets import QWidget
from shiboken6 import wrapInstance

from maya import OpenMayaUI

from PIK_workfile_manager_maya.core import MayaCore
from PIK_workfile_manager.ui.base import BaseOpenWindow, BaseSaveWindow


class MayaOpenWorkfileWindow(BaseOpenWindow):

    def __init__(self):
        self.backend = MayaCore() # TODO : move backend and ui association to __init__

        self.backend.workfile_open.connect(self.backend.open_workfile)

        super().__init__(parent = get_maya_main_window())


class MayaSaveWorkfileWindow(BaseSaveWindow):

    def __init__(self):
        self.backend = MayaCore()

        self.backend.workfile_save.connect(self.backend._refresh_scenes)
        self.backend.workfile_save.connect(self.backend.save_workfile)

        super().__init__(parent=get_maya_main_window())


def get_maya_main_window():
    """
    Get the maya main window object.
    Returns:
        class: `QWidget`: The maya main window object.
    """
    main_window_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QWidget)
