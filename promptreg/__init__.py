"""promptreg: pytest-style regression testing for prompts and LLM outputs.

Quick start:
    >>> from promptreg import PromptTest, Runner, contains

    >>> def call_llm(prompt: str) -> str:
    ...     return my_llm_client.generate(prompt)

    >>> tests = [
    ...     PromptTest(
    ...         name="greeting_includes_name",
    ...         prompt="Say hello to Sam in one sentence.",
    ...         fn=call_llm,
    ...         assertions=[contains("Sam")],
    ...     ),
    ... ]
    >>> report = Runner(tests, snapshot_path=".promptreg/snapshots.json").run()
    >>> report.show()
"""

from .assertions import (
    contains,
    custom,
    is_valid_json,
    json_has_keys,
    matches_regex,
    max_length,
    min_length,
    not_contains,
    similar_to,
)
from .core import PromptTest, Runner, TestResult
from .report import Report

__version__ = "0.1.0"
__all__ = [
    "PromptTest",
    "Runner",
    "TestResult",
    "Report",
    "contains",
    "not_contains",
    "matches_regex",
    "is_valid_json",
    "json_has_keys",
    "max_length",
    "min_length",
    "similar_to",
    "custom",
]
