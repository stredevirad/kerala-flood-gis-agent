# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression tests for F7 (quota classification) and F8 (gpt-oss responses)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
from openai import APIStatusError, InternalServerError, RateLimitError

from kerala.bench import run_one as run_one_module
from kerala.bench.run_one import classify_exit, run_one
from kerala.config import model_config
from src.agent.llm_engine import OpenAIEngine, describe_api_error, react_text_from_tool_calls
from src.agent.react_agent import _parse_action


def _status_error(cls, code: int, body=None, message: str = "error"):
    response = httpx.Response(code, request=httpx.Request("POST", "https://api.example.test/chat"))
    return cls(message, response=response, body=body)


def _engine_with(create):
    engine = OpenAIEngine(model="test-model", api_key="test-key", temperature=0, seed=1)
    engine.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return engine


# ---------------------------------------------------------------- F7: quota

def test_quota_label_ignores_429_inside_numeric_trace_field(monkeypatch, tmp_path):
    """The old substring check labelled this run `paused_quota`."""

    class FakeAgent:
        def __init__(self, *args, **kwargs):
            pass

        def run(self, instruction, data_dir, work_dir, on_step=None, should_stop=None):
            on_step({"round": 1, "action": "finish", "success": True, "gen_time_ms": 41429.512})
            return SimpleNamespace(total_rounds=1, success=True)

    monkeypatch.setattr(run_one_module, "KeralaAgent", FakeAgent)
    meta = run_one("D01", "pack", "stub", tmp_path / "run")
    trace = (tmp_path / "run" / "trace.jsonl").read_text(encoding="utf-8")
    assert "429" in trace
    assert meta["exit_reason"] == "finished"
    assert meta["quota_errors"] == 0


def test_stub_quota_engine_is_labelled_paused_quota(tmp_path):
    meta = run_one("D01", "pack", "stub", tmp_path / "run", stub_mode="quota")
    assert meta["exit_reason"] == "paused_quota"
    assert meta["quota_errors"] >= 1


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"quota_errors": 0, "exception": None, "rounds": 3, "success": True}, "finished"),
        ({"quota_errors": 0, "exception": None, "rounds": 16, "success": False}, "max_rounds"),
        ({"quota_errors": 0, "exception": None, "rounds": 16, "success": True}, "finished"),
        ({"quota_errors": 0, "exception": ValueError("took 429 ms"), "rounds": 0, "success": None}, "error"),
        ({"quota_errors": 2, "exception": None, "rounds": 4, "success": False}, "paused_quota"),
    ],
)
def test_classify_exit_uses_structured_signals(kwargs, expected):
    assert classify_exit(max_rounds=16, **kwargs) == expected


def test_classify_exit_recognises_rate_limit_exception():
    exc = _status_error(RateLimitError, 429)
    assert classify_exit(quota_errors=0, exception=exc, rounds=0, success=None, max_rounds=16) == "paused_quota"


def test_describe_api_error_classifies_by_type_status_and_explicit_field():
    assert describe_api_error(_status_error(RateLimitError, 429))["quota"] is True
    exhausted = _status_error(APIStatusError, 400, body={"error": {"status": "RESOURCE_EXHAUSTED"}})
    assert describe_api_error(exhausted)["quota"] is True
    as_list = _status_error(APIStatusError, 400, body=[{"error": {"status": "RESOURCE_EXHAUSTED"}}])
    assert describe_api_error(as_list)["quota"] is True
    # A server error whose message merely mentions 429 / RESOURCE_EXHAUSTED is not a quota stop.
    server = _status_error(InternalServerError, 500, message="upstream said 429 RESOURCE_EXHAUSTED")
    assert describe_api_error(server)["quota"] is False
    assert describe_api_error(ValueError("gen_time_ms=1429"))["quota"] is False


def test_engine_counts_a_persistent_rate_limit_as_a_quota_error(monkeypatch):
    monkeypatch.setattr("src.agent.llm_engine.time.sleep", lambda _s: None)
    rate_limit = _status_error(RateLimitError, 429)

    def create(**_kwargs):
        raise rate_limit

    engine = _engine_with(create)
    result = engine.generate("prompt")
    assert result["text"].startswith("Error during API call")
    assert engine.quota_errors == 1
    assert engine.last_error["status_code"] == 429


# ------------------------------------------------------------- F8: gpt-oss

def _tool_call_response(content, tool_calls, reasoning="private reasoning with Action: execute"):
    message = SimpleNamespace(content=content, tool_calls=tool_calls, reasoning=reasoning)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="tool_calls")], usage=usage)


def test_native_tool_call_becomes_react_text_without_reasoning():
    arguments = '{"op":"load_vector","inputs":{"path":"dataset/hospitals.geojson"},"output":"hospitals"}'
    call = SimpleNamespace(function=SimpleNamespace(name="geoprocess", arguments=arguments), type="function")
    engine = _engine_with(lambda **_k: _tool_call_response("", [call]))
    result = engine.generate("prompt")
    assert "private" not in result["text"]
    thought, action, args = _parse_action(result["text"])
    assert action == "geoprocess"
    assert args["op"] == "load_vector"
    assert args["inputs"]["path"] == "dataset/hospitals.geojson"
    assert engine.native_tool_calls == 1


def test_text_action_wins_over_tool_call():
    text = "Thought: t\nAction: finish\nArgs: {}"
    call = {"function": {"name": "execute", "arguments": "{}"}}
    engine = _engine_with(lambda **_k: _tool_call_response(text, [call]))
    assert engine.generate("prompt")["text"] == text
    assert engine.native_tool_calls == 0


def test_dict_tool_call_arguments_are_serialised():
    text = react_text_from_tool_calls([{"function": {"name": "load_vector", "arguments": {"path": "dataset/x.gpkg", "var_name": "x"}}}])
    _thought, action, args = _parse_action(text)
    assert action == "load_vector" and args == {"path": "dataset/x.gpkg", "var_name": "x"}


def test_empty_response_does_not_parse_as_a_tool_named_args():
    engine = _engine_with(lambda **_k: _tool_call_response(None, None))
    _thought, action, _args = _parse_action(engine.generate("prompt")["text"])
    assert action == ""


def test_reasoning_effort_is_sent_only_when_configured():
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return _tool_call_response("Thought: t\nAction: finish\nArgs: {}", None)

    engine = _engine_with(create)
    engine.generate("prompt")
    engine.reasoning_effort = "low"
    engine.generate("prompt")
    assert "reasoning_effort" not in calls[0]
    assert calls[1]["reasoning_effort"] == "low"


def test_gptoss_config_uses_low_reasoning_and_8192_tokens():
    config = model_config("pc-gptoss20b")
    assert config["reasoning_effort"] == "low"
    assert config["max_tokens"] == 8192
