from abc import ABCMeta

from PySide6 import QtCore

from rez_production_context import get_context_from_env
from rez_production_context.contexts import (
    Studio,
    Project,
    AssetType,
    Asset,
    Sequence,
    Shot,
)

from PIK_path_manager import ProductionPath

from PIK_workfile_manager.validations import valid_folder_path, valid_extension


class QABCMeta(type(QtCore.QObject), ABCMeta):
    """Metaclass combining Qt's metaclass with ABCMeta.

    Shiboken's ``ObjectType.__new__`` calls ``type.__new__`` directly, so
    ``ABCMeta.__new__`` never runs and ``__abstractmethods__`` is never
    populated. We compute it ourselves and enforce it in ``__call__``.
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        abstracts = {
            attr
            for attr, value in namespace.items()
            if getattr(value, "__isabstractmethod__", False)
        }
        for base in bases:
            for attr in getattr(base, "__abstractmethods__", ()):
                value = getattr(cls, attr, None)
                if getattr(value, "__isabstractmethod__", False):
                    abstracts.add(attr)

        cls.__abstractmethods__ = frozenset(abstracts)
        return cls

    def __call__(cls, *args, **kwargs):
        abstracts = getattr(cls, "__abstractmethods__", frozenset())
        if abstracts:
            raise TypeError(
                f"Can't instantiate abstract class {cls.__name__} "
                f"with abstract methods: {', '.join(sorted(abstracts))}"
            )
        return super().__call__(*args, **kwargs)


def get_existing_scene_names(folder_path: str, extension: str) -> list[str]:
    folder_path = valid_folder_path(folder_path)
    extension = valid_extension(extension)

    existing_scene_files = [
        ProductionPath(folder_path / file) for file in folder_path.glob(f"*.{extension}")
    ]
    existing_scene_names = set()

    for file in existing_scene_files:
        datas = file.as_data()
        existing_scene_names.add(datas["scene_name"])

    if existing_scene_names:
        return list(existing_scene_names)
    else:
        return []


def get_existing_scene_versions(folder_path: str, scene_name: str, extension: str) -> list[str]:
    folder_path = valid_folder_path(folder_path)
    extension = valid_extension(extension)

    existing_scene_files = [
        ProductionPath(folder_path / file) for file in folder_path.glob(f"*.{extension}")
    ]
    existing_scene_versions = set()

    for file in existing_scene_files:
        datas = file.as_data()
        if datas["scene_name"] == scene_name:
            existing_scene_versions.add(datas["version"])

    if existing_scene_versions:
        return list(existing_scene_versions)
    else:
        return []
