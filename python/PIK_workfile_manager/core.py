from abc import ABCMeta

from PySide6 import QtCore

from difflib import SequenceMatcher
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

from python.PIK_workfile_manager.constants import MAX_ENTITY_DISPLAY, MAX_ENTITY_LOAD


class QABCMeta(type(QtCore.QObject), ABCMeta):
    """Metaclass combining Qt's metaclass with ABCMeta.

    Shiboken bypasses ``object.__new__``, so the abstract-method check
    is done explicitly to guarantee abstract classes can't be instantiated.
    """

    def __call__(cls, *args, **kwargs):
        if cls.__abstractmethods__:
            raise TypeError(
                f"Can't instantiate abstract class {cls.__name__} "
                f"with abstract methods: {', '.join(sorted(cls.__abstractmethods__))}"
            )
        return super().__call__(*args, **kwargs)


def find_closest_strings(
    user_input: str, available_strings: list[str], threshold: float = 0.4
):
    """
    Find the strings that most closely match the user's input.

    Matching is based on string similarity, with an additional weight given
    to candidates that start with the user's input. Results are ordered from
    the closest to the least similar match.

    Args:
        user_input: The string to search for.
        available_strings: The strings to compare against.
        threshold: Minimum similarity score required for a match.

    Returns:
        A list of the closest matching strings, ordered by relevance.
    """

    if user_input == "*":
        return available_strings

    scored = []

    for value in available_strings:
        candidate = value.lower()

        similarity = SequenceMatcher(None, user_input, candidate).ratio()

        if candidate.startswith(user_input):
            similarity += 0.5

        if similarity >= threshold:
            scored.append((value, similarity))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [value for value, _ in scored]
