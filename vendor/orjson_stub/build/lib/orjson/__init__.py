"""
Fallback implementation of the :mod:`orjson` API used by the project.

The real orjson package ships native wheels that are unavailable in the
restricted environment we work in here.  This lightweight shim preserves the
same interface (`dumps` returning bytes, `loads` accepting bytes/str) by
delegating to Python's built-in :mod:`json` module.
"""

from __future__ import annotations

import json
from typing import Any

__all__ = ["dumps", "loads"]


def dumps(value: Any, *, default: Any = None, option: Any = None) -> bytes:
    """Serialize *value* to UTF-8 encoded JSON bytes."""

    if default is not None:
        return json.dumps(value, default=default).encode("utf-8")
    return json.dumps(value).encode("utf-8")


def loads(data: bytes | str) -> Any:
    """Deserialize JSON bytes/str into Python objects."""

    if isinstance(data, (bytes, bytearray)):
        data = data.decode("utf-8")
    return json.loads(data)
