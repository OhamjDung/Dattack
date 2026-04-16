from typing import Any, Optional

_store: dict[str, dict[str, Any]] = {}


def save(session_id: str, data: dict[str, Any]) -> None:
    _store[session_id] = data


def update(session_id: str, partial: dict[str, Any]) -> None:
    existing = _store.get(session_id, {})
    _store[session_id] = {**existing, **partial}


def get(session_id: str) -> Optional[dict[str, Any]]:
    return _store.get(session_id)


def delete(session_id: str) -> None:
    _store.pop(session_id, None)
