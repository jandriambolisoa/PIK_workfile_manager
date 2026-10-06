name = "PIK_workfile_manager"

version = "0.0.1"

authors = [
    "Jeremy Andriambolisoa",
]

description = \
    """
    A cross-DCC workfile manager for Piktura's pipeline.
    """

requires = [
    "rez_production_context",
    "PIK_path_manager"
]

uuid = "piktura.PIK_maya_loader"

build_command = 'python {root}/build.py {install}'

def commands():
    env.PYTHONPATH.append("{root}/python")
    env.MAYA_MODULE_PATH.append("{root}/python/PIK_maya_loader/module")