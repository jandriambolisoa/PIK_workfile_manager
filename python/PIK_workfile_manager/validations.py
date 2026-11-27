import re

def valid_scene_name(scene_name: str) -> str:
    """
    Validate a scene name.

    A valid scene name may only contain letters and underscores.
    The validated name is returned unchanged.

    Args:
        scene_name: Scene name to validate.

    Returns:
        The validated scene name.

    Raises:
        ValueError: If the scene name contains invalid characters.
    """
    if bool(re.fullmatch(r"[A-Za-z_]+", scene_name)):
        return scene_name
    else:
        raise ValueError(f"Invalid scene name: {scene_name}")