import json
import os
import tempfile

import pytest

from promptreg import (
    PromptTest,
    Runner,
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
from promptreg.core import run_test


def const_fn(value):
    return lambda prompt: value


def test_contains_pass_and_fail():
    test = PromptTest(name="t", prompt="p", fn=const_fn("Hello Sam!"), assertions=[contains("Sam")], snapshot=False)
    result = run_test(test)
    assert result.passed

    test2 = PromptTest(name="t2", prompt="p", fn=const_fn("Hello there"), assertions=[contains("Sam")], snapshot=False)
    result2 = run_test(test2)
    assert not result2.passed
    assert "Sam" in result2.assertion_outcomes[0].message


def test_not_contains():
    test = PromptTest(name="t", prompt="p", fn=const_fn("clean output"), assertions=[not_contains("error")], snapshot=False)
    assert run_test(test).passed


def test_matches_regex():
    test = PromptTest(name="t", prompt="p", fn=const_fn("Order #12345 confirmed"), assertions=[matches_regex(r"#\d+")], snapshot=False)
    assert run_test(test).passed


def test_is_valid_json_pass_and_fail():
    good = PromptTest(name="t", prompt="p", fn=const_fn('{"a": 1}'), assertions=[is_valid_json()], snapshot=False)
    assert run_test(good).passed

    bad = PromptTest(name="t", prompt="p", fn=const_fn("not json"), assertions=[is_valid_json()], snapshot=False)
    assert not run_test(bad).passed


def test_json_has_keys():
    test = PromptTest(
        name="t", prompt="p", fn=const_fn(json.dumps({"name": "Sam", "age": 30})),
        assertions=[json_has_keys("name", "age")], snapshot=False,
    )
    assert run_test(test).passed

    test_missing = PromptTest(
        name="t", prompt="p", fn=const_fn(json.dumps({"name": "Sam"})),
        assertions=[json_has_keys("name", "age")], snapshot=False,
    )
    result = run_test(test_missing)
    assert not result.passed
    assert "age" in result.assertion_outcomes[0].message


def test_max_min_length():
    test = PromptTest(name="t", prompt="p", fn=const_fn("short"), assertions=[max_length(10), min_length(2)], snapshot=False)
    assert run_test(test).passed

    test_too_long = PromptTest(name="t", prompt="p", fn=const_fn("this is way too long"), assertions=[max_length(5)], snapshot=False)
    assert not run_test(test_too_long).passed


def test_similar_to():
    test = PromptTest(name="t", prompt="p", fn=const_fn("The cat sat on the mat"), assertions=[similar_to("The cat sat on the mat", threshold=0.99)], snapshot=False)
    assert run_test(test).passed

    test_diff = PromptTest(name="t", prompt="p", fn=const_fn("Completely unrelated text here"), assertions=[similar_to("The cat sat on the mat", threshold=0.9)], snapshot=False)
    assert not run_test(test_diff).passed


def test_custom_assertion():
    is_upper = custom(lambda o: o.isupper(), name="is_upper", failure_message="expected uppercase output")
    test = PromptTest(name="t", prompt="p", fn=const_fn("SHOUTING"), assertions=[is_upper], snapshot=False)
    assert run_test(test).passed


def test_error_in_fn_is_captured_not_raised():
    def broken_fn(prompt):
        raise ValueError("API timeout")

    test = PromptTest(name="t", prompt="p", fn=broken_fn, snapshot=False)
    result = run_test(test)
    assert not result.passed
    assert "API timeout" in result.error


def test_repeat_flags_inconsistency():
    outputs = iter(["A", "B"])
    test = PromptTest(name="t", prompt="p", fn=lambda p: next(outputs), repeat=2, snapshot=False)
    result = run_test(test)
    assert not result.passed
    assert "consistency" in result.assertion_outcomes[0].name


def test_repeat_passes_when_consistent():
    test = PromptTest(name="t", prompt="p", fn=const_fn("same"), repeat=3, snapshot=False)
    assert run_test(test).passed


def test_snapshot_new_then_unchanged_then_changed():
    with tempfile.TemporaryDirectory() as d:
        snap_path = os.path.join(d, "snapshots.json")

        test = PromptTest(name="greeting", prompt="p", fn=const_fn("Hello!"), snapshot=True)
        runner = Runner([test], snapshot_path=snap_path)

        # First run: no prior snapshot -> "new".
        report1 = runner.run(update_snapshots=True)
        assert report1.results[0].snapshot_diff == "new"

        # Second run, same output: "unchanged".
        report2 = runner.run()
        assert report2.results[0].snapshot_diff == "unchanged"

        # Third run, output drifted: "changed".
        test_changed = PromptTest(name="greeting", prompt="p", fn=const_fn("Hi there!"), snapshot=True)
        runner_changed = Runner([test_changed], snapshot_path=snap_path)
        report3 = runner_changed.run()
        assert report3.results[0].snapshot_diff == "changed"
        assert len(report3.changed) == 1


def test_runner_report_aggregation():
    tests = [
        PromptTest(name="pass1", prompt="p", fn=const_fn("Sam is here"), assertions=[contains("Sam")], snapshot=False),
        PromptTest(name="fail1", prompt="p", fn=const_fn("no match"), assertions=[contains("Sam")], snapshot=False),
    ]
    report = Runner(tests).run()
    assert len(report) == 2
    assert report.n_passed == 1
    assert report.n_failed == 1
    assert not report.all_passed()
    assert report.failures[0].test_name == "fail1"


def test_tag_filtering():
    tests = [
        PromptTest(name="a", prompt="p", fn=const_fn("x"), tags=["fast"], snapshot=False),
        PromptTest(name="b", prompt="p", fn=const_fn("x"), tags=["slow"], snapshot=False),
    ]
    report = Runner(tests).run(tags=["fast"])
    assert len(report) == 1
    assert report.results[0].test_name == "a"
