import os
import os.path
import shutil
import sys

from typing import List

def get_source_folders() -> List[str]:
    """Get the sources directories to copy during build/install based on resolved packages.

    Returns:
        List[str]: List of source directories to copy.
    """
    source_directories = ["python"]

    resolved_packages = os.environ.get("REZ_USED_RESOLVE", "").split(" ")
    resolved_packages_names = [package.split("-")[0] for package in resolved_packages]

    if "maya" in  resolved_packages_names:
        source_directories.append("maya")

    if "houdini" in resolved_packages_names:
        source_directories.append("houdini")

    return source_directories

def build(source_path, build_path, install_path, targets):

    def _build():
        for folder in get_source_folders():
            src_py = os.path.join(source_path, folder)
            dest_py = os.path.join(build_path, folder)

            if not os.path.exists(dest_py):
                shutil.copytree(src_py, dest_py)

    def _install():
        for folder in get_source_folders():
            src = os.path.join(build_path, folder)
            dest = os.path.join(install_path, folder)

            if os.path.exists(dest):
                shutil.rmtree(dest)

            shutil.copytree(src, dest)

    _build()

    if "install" in (targets or []):
        _install()


if __name__ == '__main__':
    build(
        source_path=os.environ['REZ_BUILD_SOURCE_PATH'],
        build_path=os.environ['REZ_BUILD_PATH'],
        install_path=os.environ['REZ_BUILD_INSTALL_PATH'],
        targets=sys.argv[1:]
    )