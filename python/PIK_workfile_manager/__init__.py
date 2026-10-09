from PIK_workfile_manager.dcc.maya import MayaFileOpenWindow, MayaFileSaveWindow

OpenWindow = {
    "maya": lambda x: MayaFileOpenWindow(),
}

SaveWindow = {
    "maya": lambda x: MayaFileSaveWindow(),
}
