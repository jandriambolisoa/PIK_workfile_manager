from pathlib import Path

def valid_folder_path(folder_path: str) -> Path:
    if Path(folder_path).is_dir():
        return Path(folder_path)
    else:
        raise ValueError(f"Invalid folder path: {folder_path}")

def valid_extension(extension: str):
    return extension.lower().lstrip('.')