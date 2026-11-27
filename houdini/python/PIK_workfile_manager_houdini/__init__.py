import hou

from PySide6 import QtCore

from PIK_workfile_manager_houdini.core import HoudiniCore
from PIK_workfile_manager_houdini.ui import HoudiniOpenWorkfileWindow, HoudiniSaveWorkfileWindow

def open_scene():
    open_dialog = HoudiniOpenWorkfileWindow(backend=HoudiniCore(), parent=hou.qt.mainWindow())
    open_dialog.show()

def save_scene():
    open_dialog = HoudiniSaveWorkfileWindow(backend=HoudiniCore(), parent=hou.qt.mainWindow())
    open_dialog.show()