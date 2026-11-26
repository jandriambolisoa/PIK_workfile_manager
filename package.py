name = "PIK_workfile_manager"

version = "0.1.0"

authors = [
    "Jeremy Andriambolisoa",
]

description = \
    """
    A cross-DCC workfile manager for Piktura's pipeline.
    """

variants = [["maya-2027"]]

requires = [
    "rez_production_context",
    "PIK_path_manager"
]

uuid = "piktura.workfile_manager"

build_command = 'python {root}/build.py {install}'

def commands():
    env.PYTHONPATH.append("{root}/python")

    if "maya" in resolve:
        env.PYTHONPATH.append("{root}/maya/python")
        env.PYTHONPATH.append("{root}/maya/python/PIK_workfile_manager_maya")