# SPDX-License-Identifier: AGPL-3.0-or-later
"""Ensure reasoning traces never reach the GIS ReAct parser."""

from types import SimpleNamespace

from src.agent.llm_engine import OpenAIEngine


def test_openai_engine_returns_only_final_text_from_reasoning_response():
    final_text = "Thought: answer the task\nAction: finish\nArgs: {}"
    message = SimpleNamespace(
        content=(
            "<think>private scratch work with an Action: execute line</think>\n"
            "<|channel|>analysis\nprivate analysis\n"
            "<|channel|>final\n"
            f"{final_text}"
        ),
        reasoning_content="separate private reasoning field",
        thinking="separate private thinking field",
    )
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        usage=None,
    )
    engine = OpenAIEngine(
        model="pc-gptoss20b",
        api_key="ollama",
        base_url="http://localhost:11434/v1",
        temperature=0,
        max_tokens=4096,
    )
    engine.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_kwargs: response)
        )
    )

    result = engine.generate("prompt")

    assert result["text"] == final_text
    assert "private" not in result["text"]
    assert "Action: execute" not in result["text"]
