from maya import cmds, OpenMaya, mel

MENU_NAME = "Workfile Manager"
"""
Name of the custom Maya menu displayed in the main menu bar.
"""

def setup():
    """
    Create and register the Workfile Manager menu in Maya.

    If a menu with the same name already exists, it is removed
    and recreated. The menu provides quick access to the
    workfile open and save tools.
    """
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