from maya import cmds, OpenMaya, mel

MENU_NAME = "Workfile Manager"

def setup():
    gMainWindow = mel.eval("$tmpVar = $gMainWindow")

    if cmds.menu(MENU_NAME, exists=True):
        cmds.deleteUI(MENU_NAME)

    menu = cmds.menu(MENU_NAME, parent=gMainWindow)

    # OPENER
    cmds.menuItem(
        "File Open...",
        command="import PIK_workfile_manager_maya; PIK_workfile_manager_maya.launch_opener()",
        sourceType="python",
        parent=menu
    )

    # SAVER
    cmds.menuItem(
        "File Save...",
        command="import PIK_workfile_manager_maya; PIK_workfile_manager_maya.launch_saver()",
        sourceType="python",
        parent=menu
    )

cmds.evalDeferred(setup)