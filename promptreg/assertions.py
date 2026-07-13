"""Built-in assertions for checking prompt/LLM outputs.

An assertion is any callable with the signature ``(output: str) -> AssertionResult``.
Write your own by matching that signature and passing it in ``assertions=[...]``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Callable, Optional


@dataclass
class AssertionResult:
    passed: bool
    message: str


AssertionFn = Callable[[str], AssertionResult]


def contains(substring: str, case_sensitive: bool = False) -> AssertionFn:
    """Assert the output contains a given substring."""

    def _check(output: str) -> AssertionResult:
        haystack = output if case_sensitive else output.lower()
        needle = substring if case_sensitive else substring.lower()
        passed = needle in haystack
        return AssertionResult(
            passed,
            f"expected output to contain {substring!r}" if not passed else "ok",
        )

    _check.__name__ = f"contains({substring!r})"
    return _check


def not_contains(substring: str, case_sensitive: bool = False) -> AssertionFn:
    """Assert the output does NOT contain a given substring."""

    def _check(output: str) -> AssertionResult:
        haystack = output if case_sensitive else output.lower()
        needle = substring if case_sensitive else substring.lower()
        passed = needle not in haystack
        return AssertionResult(
            passed,
            f"expected output to NOT contain {substring!r}" if not passed else "ok",
        )

    _check.__name__ = f"not_contains({substring!r})"
    return _check


def matches_regex(pattern: str, flags: int = 0) -> AssertionFn:
    """Assert the output matches a regex pattern (search, not full match)."""
    compiled = re.compile(pattern, flags)

    def _check(output: str) -> AssertionResult:
        passed = compiled.search(output) is not None
        return AssertionResult(
            passed,
            f"expected output to match /{pattern}/" if not passed else "ok",
        )

    _check.__name__ = f"matches_regex({pattern!r})"
    return _check


def is_valid_json() -> AssertionFn:
    """Assert the output parses as valid JSON."""

    def _check(output: str) -> AssertionResult:
        try:
            json.loads(output)
            return AssertionResult(True, "ok")
        except json.JSONDecodeError as exc:
            return AssertionResult(False, f"invalid JSON: {exc}")

    _check.__name__ = "is_valid_json()"
    return _check


def json_has_keys(*keys: str) -> AssertionFn:
    """Assert the output is a JSON object containing all given top-level keys."""

    def _check(output: str) -> AssertionResult:
        try:
            data = json.loads(output)
        except json.JSONDecodeError as exc:
            return AssertionResult(False, f"invalid JSON: {exc}")
        if not isinstance(data, dict):
            return AssertionResult(False, "expected a JSON object")
        missing = [k for k in keys if k not in data]
        passed = not missing
        return AssertionResult(
            passed,
            f"missing keys: {missing}" if missing else "ok",
        )

    _check.__name__ = f"json_has_keys{keys}"
    return _check


def max_length(n: int, unit: str = "chars") -> AssertionFn:
    """Assert the output is at most n characters (unit='chars') or words (unit='words')."""

    def _check(output: str) -> AssertionResult:
        length = len(output) if unit == "chars" else len(output.split())
        passed = length <= n
        return AssertionResult(
            passed,
            f"output is {length} {unit}, expected <= {n}" if not passed else "ok",
        )

    _check.__name__ = f"max_length({n}, unit={unit!r})"
    return _check


def min_length(n: int, unit: str = "chars") -> AssertionFn:
    """Assert the output is at least n characters (unit='chars') or words (unit='words')."""

    def _check(output: str) -> AssertionResult:
        length = len(output) if unit == "chars" else len(output.split())
        passed = length >= n
        return AssertionResult(
            passed,
            f"output is {length} {unit}, expected >= {n}" if not passed else "ok",
        )

    _check.__name__ = f"min_length({n}, unit={unit!r})"
    return _check


def similar_to(reference: str, threshold: float = 0.7) -> AssertionFn:
    """Assert the output is textually similar to a reference string.

    Uses difflib's ratio (no embedding model / API calls required) so this
    works offline out of the box. For semantic (meaning-based) similarity,
    pass your own embedding-based assertion instead — see ``custom()``.
    """

    def _check(output: str) -> AssertionResult:
        ratio = SequenceMatcher(None, output, reference).ratio()
        passed = ratio >= threshold
        return AssertionResult(
            passed,
            f"similarity {ratio:.2f} below threshold {threshold}" if not passed else "ok",
        )

    _check.__name__ = f"similar_to(threshold={threshold})"
    return _check


def custom(fn: Callable[[str], bool], name: Optional[str] = None, failure_message: str = "custom check failed") -> AssertionFn:
    """Wrap an arbitrary ``output -> bool`` function as an assertion."""

    def _check(output: str) -> AssertionResult:
        passed = bool(fn(output))
        return AssertionResult(passed, failure_message if not passed else "ok")

    _check.__name__ = name or getattr(fn, "__name__", "custom()")
    return _check
