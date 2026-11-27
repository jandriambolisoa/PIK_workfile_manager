from PySide6.QtWidgets import QWidget
from shiboken6 import wrapInstance

from PIK_workfile_manager.ui.base import BaseOpenWindow, BaseSaveWindow


class HoudiniOpenWorkfileWindow(BaseOpenWindow):

    def __init__(self, backend=None, parent=None):
        super().__init__(backend=backend, parent=parent)

    def closeEvent(self, event):
        self.setParent(None)
        super().closeEvent(event)


class HoudiniSaveWorkfileWindow(BaseSaveWindow):

    def __init__(self, backend=None, parent=None):
        super().__init__(backend=backend, parent=parent)

    def closeEvent(self, event):
        self.setParent(None)
        super().closeEvent(event)
