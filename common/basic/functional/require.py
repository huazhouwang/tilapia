from typing import Any, Union


def require(statement: Any, or_error: Union[str, Exception] = None):
    if not statement:
        or_error = or_error if isinstance(or_error, Exception) else AssertionError(or_error or "raising by require")
        raise or_error


def require_not_none(obj: Any, or_error: Union[str, Exception] = None) -> Any:
    require(obj is not None, or_error or "require not none but none found")
    return obj


def require_none(obj: Any, or_error: Union[str, Exception] = None):
    require(obj is None, or_error or f"require none but {repr(obj)} found")
