"""
Reusable typed marks.

Using pytest.mark.xxxx does not have work with mypy for some reason.
Use these variables to prevent having to #type: ignore each time a test gets marked.
"""

from typing import Callable, List, TypeVar

import pytest

Typ = TypeVar("Typ")
parametrize: Callable[[str, List], Callable[[Typ], Typ]] = pytest.mark.parametrize  # type: ignore
