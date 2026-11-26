from PIK_workfile_manager_maya.ui import MayaOpenWorkfileWindow, MayaSaveWorkfileWindow


def launch_opener():
    opener_window = MayaOpenWorkfileWindow()
    opener_window.show()

def launch_saver():
    saver_window = MayaSaveWorkfileWindow()
    saver_window.show()
