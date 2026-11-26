import re

# TODO : Implement scene name validation

def valid_scene_name(scene_name: str) -> str:
    if bool(re.fullmatch(r"[A-Za-z_]+", scene_name)):
        return scene_name
    else:
        raise ValueError(f"Invalid scene name: {scene_name}")