from PIK_workfile_manager_maya.core import get_maya_main_window, MayaCore
from PIK_workfile_manager.ui.base import BaseOpenWindow, BaseSaveWindow


def launch_opener():
    opener_window = BaseOpenWindow(parent= get_maya_main_window(), backend= MayaCore())
    opener_window.show()

def launch_saver():
    saver_window = BaseSaveWindow(parent= get_maya_main_window(), backend= MayaCore())
    saver_window.show()
