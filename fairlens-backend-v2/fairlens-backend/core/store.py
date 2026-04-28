"""
core/store.py
Simple in-memory store for analysis results and raw data.
Maps analysis_id -> (AnalysisResult, raw_df, encoded_X, encoded_y, model).
Cleared on restart (use Redis/DB for production persistence).
"""

from typing import Any
import threading

_store: dict[str, dict[str, Any]] = {}
_lock = threading.Lock()


def save(analysis_id: str, **kwargs):
    with _lock:
        _store[analysis_id] = kwargs


def load(analysis_id: str) -> dict[str, Any] | None:
    with _lock:
        return _store.get(analysis_id)


def delete(analysis_id: str):
    with _lock:
        _store.pop(analysis_id, None)


def list_ids() -> list[str]:
    with _lock:
        return list(_store.keys())
