# PIK_workfile_manager
A cross-DCC workfile manager for Piktura's pipeline.

## Example usage for Maya:
- Create a new folder a the base of the repository :
`PIK_wokfile_manager/maya/python/PIK_wokfile_manager_maya`

- Create the software backend : `PIK_wokfile_manager/maya/python/PIK_wokfile_manager_maya/core.py` :

- Connect the backend with the UI (see below) : `PIK_wokfile_manager/maya/python/PIK_wokfile_manager_maya/__init__.py` :
```
from PIK_workfile_manager_maya.core import get_maya_main_window, MayaCore
from PIK_workfile_manager.ui.base import BaseOpenWindow, BaseSaveWindow

def launch_opener():
    """
    Create and display the Maya workfile open window.

    The window is parented to the Maya main window and uses
    a Maya-specific backend implementation.
    """
    opener_window = BaseOpenWindow(parent= get_maya_main_window(), backend= MayaCore())
    opener_window.show()

def launch_saver():
    """
    Create and display the Maya workfile save window.

    The window is parented to the Maya main window and uses
    a Maya-specific backend implementation.
    """
    saver_window = BaseSaveWindow(parent= get_maya_main_window(), backend= MayaCore())
    saver_window.show()

```

## TO DOs
tests

docs