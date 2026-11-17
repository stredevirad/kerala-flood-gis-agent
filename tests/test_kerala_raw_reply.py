# SPDX-License-Identifier: AGPL-3.0-or-later
"""Raw model replies are logged to trace.jsonl without changing behaviour or scoring."""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
from openai import InternalServerError, OpenAI

from kerala.bench import run_one as run_one_module
from kerala.bench.run_one import _install_raw_reply_logger, _with_raw_replies
from kerala.bench.score import _trace_text
from src.agent.llm_engine import OpenAIEngine


def _response(content, tool_calls=None, reasoning=None, finish="stop"):
    message = SimpleNamespace(content=content, tool_calls=tool_calls, reasoning=reasoning)
    usage = SimpleNamespace(prompt_tokens=10, completion_tokens=5, prompt_tokens_details=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=finish)], usage=usage)


def _engine(create):
    engine = OpenAIEngine(model="test-model", api_key="k", temperature=0)
    engine.client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    return engine


def test_logger_records_raw_reply_and_leaves_engine_output_unchanged():
    call = SimpleNamespace(function=SimpleNamespace(name="geoprocess", arguments='{"op": "buffer"}'))
    response = _response("", tool_calls=[call], reasoning="private plan", finish="tool_calls")
    plain = _engine(lambda **_k: response)
    logged = _engine(lambda **_k: response)
    sink: list = []
    _install_raw_reply_logger(logged, sink)

    text_plain = plain.generate("p")["text"]
    text_logged = logged.generate("p")["text"]
    assert text_plain == text_logged  # parser input unchanged
    record = sink[-1]
    assert record["finish_reason"] == "tool_calls"
    assert record["content"] == ""
    assert record["tool_calls"] == [{"name": "geoprocess", "arguments": '{"op": "buffer"}'}]
    assert record["reasoning"] == "private plan"


def test_logger_records_error_bodies_and_reraises_for_the_engine():
    body = {"message": "error parsing tool call: raw='print(1)\n', err=invalid character"}
    error = InternalServerError("Error code: 500", response=httpx.Response(500, request=httpx.Request("POST", "http://x")), body=body)

    def create(**_k):
        raise error

    engine = _engine(create)
    sink: list = []
    _install_raw_reply_logger(engine, sink)
    text = engine.generate("p")["text"]
    assert "Action: execute" in text  # the engine's F8 recovery still sees the original exception
    assert sink == [{"error_type": "InternalServerError", "status_code": 500, "body": body}]


def test_logger_installs_on_a_real_openai_client():
    client = OpenAI(api_key="k", base_url="http://localhost:9/v1", max_retries=0)
    engine = SimpleNamespace(client=client)
    sink: list = []
    _install_raw_reply_logger(engine, sink)
    assert client.chat.completions.create.__name__ == "logged_create"


def test_events_carry_raw_replies_and_sink_is_drained():
    events: list = []
    sink = [{"content": "a"}, {"content": "b"}]
    on_step = _with_raw_replies(events, sink)
    on_step({"round": 1, "action": "finish"})
    on_step({"round": 2, "action": "finish"})
    assert events[0]["raw_replies"] == [{"content": "a"}, {"content": "b"}]
    assert events[1]["raw_replies"] == []
    assert sink == []


def test_stub_run_writes_raw_replies_key(tmp_path):
    run_one_module.run_one("D01", "pack", "stub", tmp_path / "run")
    lines = (tmp_path / "run" / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert lines and all("raw_replies" in json.loads(line) for line in lines)


def test_scorer_ignores_raw_replies(tmp_path):
    base = {"round": 1, "action": "execute", "observation_full": "ok"}
    noisy = dict(base, raw_replies=[{"content": "Traceback geoprocess trimmed"}])
    with_raw = tmp_path / "with.jsonl"
    without = tmp_path / "without.jsonl"
    with_raw.write_text(json.dumps(noisy, ensure_ascii=False) + "\n", encoding="utf-8")
    without.write_text(json.dumps(base, ensure_ascii=False) + "\n", encoding="utf-8")
    assert _trace_text(with_raw) == _trace_text(without)
    assert "traceback" not in _trace_text(with_raw).casefold()
