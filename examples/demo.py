"""Demo using a fake 'LLM' so this runs with no API key required.

Swap `fake_llm` for a real client (OpenAI, Anthropic, etc.) to use this
for real. Run with: python examples/demo.py
"""

from promptreg import PromptTest, Runner, contains, is_valid_json, max_length


def fake_llm(prompt: str) -> str:
    """Stand-in for a real LLM call — deterministic so the demo is reproducible."""
    if "extract the name" in prompt.lower():
        return "The name is Priya."
    if "json" in prompt.lower():
        return '{"name": "Priya", "city": "Austin"}'
    if "haiku" in prompt.lower():
        return "Silent autumn wind\nLeaves fall like whispered secrets\nWinter waits nearby"
    return "I don't know how to answer that."


tests = [
    PromptTest(
        name="extracts_name",
        prompt="Extract the name from: 'Hi, I'm Priya and I live in Austin.'",
        fn=fake_llm,
        assertions=[contains("Priya")],
    ),
    PromptTest(
        name="returns_valid_json",
        prompt="Return as JSON the name and city for: 'Hi, I'm Priya from Austin.'",
        fn=fake_llm,
        assertions=[is_valid_json()],
    ),
    PromptTest(
        name="haiku_is_short",
        prompt="Write a haiku about autumn.",
        fn=fake_llm,
        assertions=[max_length(30, unit="words")],
    ),
]

if __name__ == "__main__":
    report = Runner(tests, snapshot_path=".promptreg/snapshots.json").run(update_snapshots=True)
    print(report.summary())
