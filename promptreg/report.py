"""Aggregation and rendering of test run results."""

from __future__ import annotations

from typing import List

from .core import TestResult

_DIFF_COLOR = {
    "new": "#0d6efd",
    "changed": "#dc3545",
    "unchanged": "#198754",
    None: "#6c757d",
}


class Report:
    """Holds all TestResults from a run and renders a pytest-style summary."""

    def __init__(self, results: List[TestResult]):
        self.results = results

    def __len__(self) -> int:
        return len(self.results)

    def __repr__(self) -> str:
        return f"<Report: {self.n_passed}/{len(self.results)} passed>"

    @property
    def n_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def n_failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def failures(self) -> List[TestResult]:
        return [r for r in self.results if not r.passed]

    @property
    def changed(self) -> List[TestResult]:
        """Tests whose output changed relative to the stored snapshot."""
        return [r for r in self.results if r.snapshot_diff == "changed"]

    def all_passed(self) -> bool:
        return self.n_failed == 0

    def summary(self) -> str:
        lines = []
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            diff_tag = f" [{r.snapshot_diff}]" if r.snapshot_diff else ""
            lines.append(f"{status}{diff_tag}  {r.test_name}  ({r.duration_seconds:.3f}s)")
            if not r.passed:
                if r.error:
                    lines.append(f"       ERROR: {r.error.splitlines()[0]}")
                for outcome in r.assertion_outcomes:
                    if not outcome.passed:
                        lines.append(f"       ✗ {outcome.name}: {outcome.message}")
        lines.append("")
        lines.append(f"{self.n_passed}/{len(self.results)} passed")
        if self.changed:
            lines.append(f"{len(self.changed)} output(s) changed since last snapshot")
        return "\n".join(lines)

    def to_dict(self) -> List[dict]:
        return [
            {
                "test_name": r.test_name,
                "passed": r.passed,
                "output": r.output,
                "duration_seconds": r.duration_seconds,
                "error": r.error,
                "snapshot_diff": r.snapshot_diff,
                "assertions": [
                    {"name": a.name, "passed": a.passed, "message": a.message}
                    for a in r.assertion_outcomes
                ],
            }
            for r in self.results
        ]

    def show(self) -> None:
        try:
            from IPython.display import HTML, display

            display(HTML(self._to_html()))
        except ImportError:
            print(self.summary())

    def _to_html(self) -> str:
        rows = []
        for r in self.results:
            color = "#198754" if r.passed else "#dc3545"
            status = "PASS" if r.passed else "FAIL"
            diff_color = _DIFF_COLOR.get(r.snapshot_diff)
            diff_badge = (
                f'<span style="background:{diff_color};color:white;padding:2px 6px;'
                f'border-radius:8px;font-size:0.75em;margin-left:6px;">{r.snapshot_diff}</span>'
                if r.snapshot_diff
                else ""
            )
            detail_lines = []
            if r.error:
                detail_lines.append(f"<span style='color:#dc3545;'>{r.error.splitlines()[0]}</span>")
            for a in r.assertion_outcomes:
                mark = "✓" if a.passed else "✗"
                acolor = "#198754" if a.passed else "#dc3545"
                detail_lines.append(f"<span style='color:{acolor};'>{mark} {a.name}: {a.message}</span>")
            details = "<br>".join(detail_lines)
            output_preview = (r.output or "")[:200]
            rows.append(
                f"""
                <tr>
                  <td style="padding:6px;border-bottom:1px solid #eee;">
                    <span style="background:{color};color:white;padding:2px 8px;
                    border-radius:10px;font-size:0.8em;">{status}</span>{diff_badge}
                  </td>
                  <td style="padding:6px;border-bottom:1px solid #eee;"><b>{r.test_name}</b><br>
                    <span style="color:#555;font-size:0.85em;">{details}</span></td>
                  <td style="padding:6px;border-bottom:1px solid #eee;font-size:0.8em;color:#777;">
                    {output_preview}</td>
                </tr>
                """
            )

        return f"""
        <div style="font-family:sans-serif;">
          <h3>promptreg report — {self.n_passed}/{len(self.results)} passed</h3>
          <table style="border-collapse:collapse;width:100%;">
            <tr style="text-align:left;background:#f7f7f7;">
              <th style="padding:6px;">Status</th>
              <th style="padding:6px;">Test</th>
              <th style="padding:6px;">Output preview</th>
            </tr>
            {''.join(rows)}
          </table>
        </div>
        """
