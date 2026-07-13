"""Command-line runner: `promptreg run tests_file.py`.

Discovers module-level ``PromptTest`` instances (or a list of them, e.g.
a variable named ``tests``) in the given file and runs them, printing a
pytest-style summary. Exits with code 1 if any test fails, so it plugs
into CI easily.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import List

from .core import PromptTest, Runner


def _load_tests_from_file(path: str) -> List[PromptTest]:
    module_path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(module_path.stem, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    tests: List[PromptTest] = []
    for value in vars(module).values():
        if isinstance(value, PromptTest):
            tests.append(value)
        elif isinstance(value, (list, tuple)):
            tests.extend([v for v in value if isinstance(v, PromptTest)])

    # De-duplicate in case a test is both module-level and inside a list.
    seen = set()
    unique_tests = []
    for t in tests:
        if id(t) not in seen:
            seen.add(id(t))
            unique_tests.append(t)
    return unique_tests


def main(argv: List[str] = None) -> int:
    parser = argparse.ArgumentParser(prog="promptreg", description="Regression testing for prompts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run prompt tests from a Python file.")
    run_parser.add_argument("file", help="Path to a Python file defining PromptTest objects.")
    run_parser.add_argument(
        "--snapshot-path",
        default=".promptreg/snapshots.json",
        help="Path to the snapshot file (default: .promptreg/snapshots.json).",
    )
    run_parser.add_argument(
        "--update-snapshots",
        action="store_true",
        help="Overwrite stored snapshots with this run's outputs.",
    )
    run_parser.add_argument("--tags", nargs="*", default=None, help="Only run tests matching any of these tags.")

    args = parser.parse_args(argv)

    if args.command == "run":
        tests = _load_tests_from_file(args.file)
        if not tests:
            print(f"No PromptTest objects found in {args.file}")
            return 1

        runner = Runner(tests, snapshot_path=args.snapshot_path)
        report = runner.run(update_snapshots=args.update_snapshots, tags=args.tags)
        print(report.summary())
        return 0 if report.all_passed() else 1

    return 1


if __name__ == "__main__":
    sys.exit(main())
