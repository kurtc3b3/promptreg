# promptreg

Pytest-style regression testing for prompts. Catch it when a prompt tweak,
model upgrade, or system-prompt change silently breaks your outputs.

```bash
pip install promptreg
```

## Quick start

```python
from promptreg import PromptTest, Runner, contains, is_valid_json

def call_llm(prompt: str) -> str:
    # your own wrapper around OpenAI / Anthropic / a local model / whatever
    return my_client.generate(prompt)

tests = [
    PromptTest(
        name="extracts_name",
        prompt="Extract the name from: 'Hi, I'm Priya and I live in Austin.'",
        fn=call_llm,
        assertions=[contains("Priya")],
    ),
    PromptTest(
        name="returns_valid_json",
        prompt="Return {\"name\": ..., \"city\": ...} for: 'Hi, I'm Priya from Austin.'",
        fn=call_llm,
        assertions=[is_valid_json()],
    ),
]

report = Runner(tests, snapshot_path=".promptreg/snapshots.json").run()
report.show()          # HTML table in Jupyter, plain text elsewhere
assert report.all_passed()
```

## Two layers of protection

1. **Assertions** — explicit checks you write (`contains`, `matches_regex`,
   `is_valid_json`, `max_length`, `similar_to`, or your own `custom(fn)`).
2. **Snapshots** — even tests with zero assertions get compared against
   their last-recorded output, so you find out when something changed
   even if you didn't think to check for it.

```python
report = Runner(tests, snapshot_path=".promptreg/snapshots.json").run()
for r in report.changed:
    print(f"{r.test_name} output changed since last run:\n{r.output}")

# once you've reviewed and accept the new outputs as the new baseline:
Runner(tests, snapshot_path=".promptreg/snapshots.json").run(update_snapshots=True)
```

## CLI (CI-friendly)

Define tests as module-level `PromptTest` objects (or a list called
`tests`) in a Python file, then:

```bash
promptreg run my_prompt_tests.py
promptreg run my_prompt_tests.py --update-snapshots
promptreg run my_prompt_tests.py --tags fast
```

Exits with code 1 if any test fails — drop it into a CI pipeline like any
other test command.

## Built-in assertions

| Function | Checks |
|---|---|
| `contains(s)` / `not_contains(s)` | substring presence/absence |
| `matches_regex(pattern)` | regex search |
| `is_valid_json()` | output parses as JSON |
| `json_has_keys(*keys)` | JSON object has expected top-level keys |
| `max_length(n)` / `min_length(n)` | length in chars or words |
| `similar_to(reference, threshold)` | difflib text similarity (no API calls) |
| `custom(fn)` | wrap any `output -> bool` function |

## Design

- **Model-agnostic**: `fn` is just `str -> str`. Call OpenAI, Anthropic,
  a local model, or a whole agent pipeline — promptreg doesn't care.
- **No network calls of its own**: promptreg never calls an LLM; you bring
  the call, it brings the checks.
- **Flaky-prompt detection**: set `repeat=3` on a test to catch prompts
  that give inconsistent answers across runs.

## Roadmap

- [ ] Cost/token tracking per test run
- [ ] Parallel test execution
- [ ] Semantic similarity assertion via pluggable embedding function
- [ ] pytest plugin (`pytest --promptreg`) for teams already on pytest

## Contributing

New assertions are the easiest contribution: add a function to
`promptreg/assertions.py` matching `(output: str) -> AssertionResult` and
a test in `tests/`.

## License

MIT
