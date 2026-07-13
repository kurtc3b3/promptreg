"""Core test definition and execution."""

from __future__ import annotations

import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional

from .assertions import AssertionFn, AssertionResult

PromptFn = Callable[[str], str]


@dataclass
class PromptTest:
    """A single prompt regression test case.

    Args:
        name: Unique identifier for this test, used in reports and snapshots.
        prompt: The input prompt to send.
        fn: Callable that takes the prompt string and returns the model's
            output string. This is your own wrapper around whichever LLM
            API/SDK you use — promptreg never calls a model itself.
        assertions: List of assertion functions (see ``promptreg.assertions``).
            A test with no assertions still runs and records output, useful
            for pure snapshot-diffing.
        snapshot: If True, compare this test's output against the last saved
            snapshot and flag drift even without explicit assertions.
        tags: Optional labels for filtering (e.g. ["fast", "regex"]).
        repeat: Run the prompt this many times and treat any inconsistency
            across runs as a failure — useful for catching flaky/non-deterministic
            prompts. Default 1 (no repetition check).
    """

    name: str
    prompt: str
    fn: PromptFn
    assertions: List[AssertionFn] = field(default_factory=list)
    snapshot: bool = True
    tags: List[str] = field(default_factory=list)
    repeat: int = 1


@dataclass
class AssertionOutcome:
    name: str
    passed: bool
    message: str


@dataclass
class TestResult:
    test_name: str
    output: Optional[str]
    passed: bool
    assertion_outcomes: List[AssertionOutcome]
    duration_seconds: float
    error: Optional[str] = None
    snapshot_diff: Optional[str] = None  # "new" | "changed" | "unchanged" | None
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"<TestResult {self.test_name}: {status}>"


def run_test(test: PromptTest) -> TestResult:
    """Execute a single PromptTest and return its result.

    Errors raised by ``test.fn`` are caught and recorded as a failure rather
    than propagating, so one broken test doesn't abort a whole suite run.
    """
    start = time.time()
    try:
        outputs = [test.fn(test.prompt) for _ in range(max(1, test.repeat))]
    except Exception as exc:  # noqa: BLE001
        duration = time.time() - start
        return TestResult(
            test_name=test.name,
            output=None,
            passed=False,
            assertion_outcomes=[],
            duration_seconds=duration,
            error=f"{exc.__class__.__name__}: {exc}\n{traceback.format_exc()}",
            tags=test.tags,
        )
    duration = time.time() - start

    output = outputs[0]
    outcomes: List[AssertionOutcome] = []
    all_passed = True

    if test.repeat > 1 and len(set(outputs)) > 1:
        all_passed = False
        outcomes.append(
            AssertionOutcome(
                name=f"consistency(repeat={test.repeat})",
                passed=False,
                message=f"got {len(set(outputs))} distinct outputs across {test.repeat} runs",
            )
        )

    for assertion_fn in test.assertions:
        result: AssertionResult = assertion_fn(output)
        outcomes.append(
            AssertionOutcome(
                name=getattr(assertion_fn, "__name__", "assertion"),
                passed=result.passed,
                message=result.message,
            )
        )
        if not result.passed:
            all_passed = False

    return TestResult(
        test_name=test.name,
        output=output,
        passed=all_passed,
        assertion_outcomes=outcomes,
        duration_seconds=duration,
        tags=test.tags,
    )


class Runner:
    """Runs a collection of PromptTests and aggregates results into a Report."""

    def __init__(self, tests: List[PromptTest], snapshot_path: Optional[str] = None):
        self.tests = tests
        self.snapshot_path = snapshot_path

    def run(self, update_snapshots: bool = False, tags: Optional[List[str]] = None) -> "Report":
        from .report import Report
        from .snapshot import SnapshotStore

        store = SnapshotStore(self.snapshot_path) if self.snapshot_path else None
        selected = self.tests
        if tags:
            selected = [t for t in self.tests if set(t.tags) & set(tags)]

        results: List[TestResult] = []
        for test in selected:
            result = run_test(test)

            if store is not None and test.snapshot and result.output is not None:
                diff_kind = store.compare(test.name, result.output)
                result.snapshot_diff = diff_kind
                if update_snapshots:
                    store.update(test.name, result.output)

            results.append(result)

        if store is not None and update_snapshots:
            store.save()

        return Report(results)
