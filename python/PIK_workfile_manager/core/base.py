import re
from abc import ABC, abstractmethod
from pathlib import Path
from collections import defaultdict
from PySide6.QtCore import QObject, Signal, Slot

from rez_production_context import get_context_from_env
from rez_production_context.contexts import Asset, Shot
from PIK_path_manager import ProductionPath

from PIK_workfile_manager.core.constants import DEFAULT_FILENAME


class BaseCore(QObject):

    workfile_open = Signal(Path)
    workfile_save = Signal(Path, bool)

    @abstractmethod
    def __init__(self, software: str, extension: str):
        super().__init__()
        self.software = software
        self.extension = extension
        self.context = get_context_from_env()

        self.scenes = defaultdict(list) #dict[str, list[Path]]

    def _refresh_scenes(self):
        self.scenes.clear()

        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v001",
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": DEFAULT_FILENAME,
                    "version": "v001",
                }
            )

        all_files = sorted(ProductionPath.from_canonical(filepath.parent).glob("*"))

        for file in all_files:
            if not file.is_file():
                continue
            match = re.match(rf"[a-zA-Z]+_[a-zA-Z]+_(.+?)_v[0-9]+\.[a-zA-Z:{self.extension}]+", str(file.name))
            if match:
                self.scenes[match.group(1)].append(file)


    def _next_version(self, scene_name: str = DEFAULT_FILENAME) -> Path:
        versions = self.scenes.get(scene_name, None)

        if versions:
            versions.sort()
            match = re.search(r"_v([0-9]+)\.", versions[-1].name)
            if match:
                version = "v{:03d}".format(int(match.group(1)) + 1)
            else:
                version = "v001"
        else:
            version = "v001"

        if isinstance(self.context, Asset):
            return ProductionPath.from_data(
                {
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": scene_name,
                    "version": version,
                }
            )

        else:
            # Shot context
            return ProductionPath.from_data(
                {
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": scene_name,
                    "version": version,
                }
            )

    def _get_scene_version_value(self, filepath: Path) -> int:
        match = re.search(r"_v([0-9]+)\.", filepath.name)
        if match:
            return int(match.group(1))
        else:
            return 0

    def _context_as_string(self):
        if isinstance(self.context, Asset):
            return f"Project: {self.context.project.name} | Asset type: {self.context.asset_type.name} | Asset: {self.context.name} | Step: {self.context.step}"
        else:
            # Shot context
            return f"Project: {self.context.project.name} | Sequence: {self.context.sequence.name} | Shot: {self.context.name} | Step: {self.context.step}"

    def generate_save_workfile_filepath(self, scene_name: str = DEFAULT_FILENAME, version: int = 1):
        if isinstance(self.context, Asset):
            filepath = ProductionPath.from_data(
                {
                    "project": self.context.project.name,
                    "asset_type": self.context.asset_type.name,
                    "asset_name": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": scene_name,
                    "version": f"v{version:03d}",
                }
            )

        else:
            # Shot context
            filepath = ProductionPath.from_data(
                {
                    "project": self.context.project.name,
                    "sequence": self.context.sequence.name,
                    "shot": self.context.name,
                    "step": self.context.step,
                    "software": self.software,
                    "ext": self.extension,
                    "scene_name": scene_name,
                    "version": f"v{version:03d}",
                }
            )

        return ProductionPath.from_canonical(filepath)

    @Slot(Path)
    @abstractmethod
    def open_workfile(self, filepath: Path) -> Path:
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not filepath.suffix.lower().lstrip(".") in self.extension:
            raise ValueError(f"Invalid file type: {filepath}")

        return filepath

    @Slot(Path, bool)
    @abstractmethod
    def save_workfile(self, filepath: Path, force: bool = False) -> Path:
        if not force and filepath.exists():
            raise FileExistsError(f"File already exists: {filepath}")

        if not filepath.suffix.lower().lstrip(".") in self.extension:
            raise ValueError(f"Invalid file type: {filepath}")

        filepath.mkdir(parents=True, exist_ok=True)

        return filepath
