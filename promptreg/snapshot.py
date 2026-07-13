"""Snapshot storage: compare current outputs against last-saved baselines.

This is the "regression" half of promptreg — even a test with zero explicit
assertions can catch "hey, this prompt's output silently changed" the same
way pytest's snapshot-testing plugins catch UI/output diffs.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional


class SnapshotStore:
    """Loads/saves a JSON file mapping test name -> last-known output."""

    def __init__(self, path: str):
        self.path = path
        self._data: Dict[str, str] = {}
        self._dirty_updates: Dict[str, str] = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self._data = json.load(f)

    def compare(self, name: str, output: str) -> str:
        """Return 'new', 'changed', or 'unchanged' relative to the stored snapshot."""
        if name not in self._data:
            return "new"
        if self._data[name] != output:
            return "changed"
        return "unchanged"

    def get(self, name: str) -> Optional[str]:
        return self._data.get(name)

    def update(self, name: str, output: str) -> None:
        """Stage a snapshot update; call save() to persist to disk."""
        self._dirty_updates[name] = output

    def save(self) -> None:
        self._data.update(self._dirty_updates)
        self._dirty_updates = {}
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, sort_keys=True)
