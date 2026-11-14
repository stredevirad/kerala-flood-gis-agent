# SPDX-License-Identifier: AGPL-3.0-or-later
"""Execute one isolated KeralaFloodBench run."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from kerala.agent import KeralaAgent, build_data_text, compose_task
from kerala.config import ROOT, model_config, read_env
from kerala.pack.pack import load_pack
from src.agent.llm_engine import OpenAIEngine


BENCH = ROOT / "kerala" / "bench"
LAYERS = ROOT / "data" / "kerala" / "layers"
MANIFEST = ROOT / "data" / "kerala" / "meta" / "data_manifest.json"


class StubEngine:
    """A deterministic no-network engine for harness tests, never used for scoring."""

    def __init__(self, mode: str = "ok"):
        self.mode = mode
        self.backoff_seconds = 0.0
        self._calls = 0

    def load_model(self) -> bool:
        return True

    def generate(self, **_kwargs: Any) -> dict[str, Any]:
        self._calls += 1
        if self.mode == "quota":
            return {"text": "Error during API call: 429 RESOURCE_EXHAUSTED", "tokens_generated": 0, "latency_ms": 1}
        if self.mode == "sleep":
            time.sleep(30)
        if self._calls == 1:
            code = (
                "import json, os\n"
                "os.makedirs('pred_results', exist_ok=True)\n"
                "json.dump({'question_id': 'D01', 'status': 'ok', 'value': 1, 'unit': 'count', "
                "'parameters_used': {}, 'assumptions': 'stub', 'method': 'stub'}, "
                "open('pred_results/answer.json','w',encoding='utf-8'))\n"
                "open('pred_results/result.csv','w',encoding='utf-8').write('value\\n1\\n')"
            )
            return {"text": f"Thought: write deterministic fixture\nAction: execute\nArgs: {{\"code\": {json.dumps(code)}}}", "tokens_generated": 8, "latency_ms": 1}
        return {"text": "Thought: complete\nAction: finish\nArgs: {\"summary\": \"stub complete\"}", "tokens_generated": 4, "latency_ms": 1}

    def get_stats(self) -> dict[str, Any]:
        return {"total_calls": self._calls, "prompt_tokens": self._calls * 100, "total_output_tokens": self._calls * 8}


def _questions() -> dict[str, dict[str, Any]]:
    import yaml
    data = yaml.safe_load((BENCH / "questions.yaml").read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data["questions"]}


def _clear_api_key_environment() -> None:
    for key in list(os.environ):
        if key.endswith("_API_KEY"):
            os.environ.pop(key, None)


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _ollama_digest(config: dict[str, Any]) -> str | None:
    if config.get("provider") != "ollama":
        return None
    endpoint = str(config["base_url"]).replace("/v1", "/api/show")
    payload = json.dumps({"name": config["model"]}).encode("utf-8")
    try:
        request = urllib.request.Request(endpoint, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8")).get("digest")
    except Exception:
        return None


def _copy_required_outputs(out: Path) -> None:
    pred = out / "pred_results"
    for name in ("answer.json",):
        source = pred / name
        if source.is_file():
            shutil.copyfile(source, out / name)


def run_one(qid: str, arm: str, model: str, out: Path, *, stub_mode: str = "ok") -> dict[str, Any]:
    """Run one question and persist the standard artifact bundle."""
    if arm not in {"noparam", "inline", "pack"}:
        raise ValueError("arm must be noparam, inline, or pack")
    question = _questions().get(qid)
    if question is None:
        raise ValueError(f"Unknown question ID: {qid}")
    config = model_config(model)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    _clear_api_key_environment()
    pack = load_pack()
    secret = read_env().get(str(config.get("api_key_env", "")), "")
    engine: Any
    if config.get("provider") == "stub":
        engine = StubEngine(stub_mode)
    else:
        engine = OpenAIEngine(
            model=str(config["model"]), api_key=secret or str(config.get("api_key", "ollama")),
            temperature=float(config.get("temperature", 0)), max_tokens=int(config.get("max_tokens", 1536)),
            base_url=str(config.get("base_url")), seed=config.get("seed"), request_timeout=600,
        )
    started = time.monotonic()
    events: list[dict[str, Any]] = []
    result = None
    caught = ""
    max_prompt_tokens = 0
    try:
        if not engine.load_model():
            raise RuntimeError("model initialization failed")
        original_generate = engine.generate

        def measured_generate(*args: Any, **kwargs: Any) -> dict[str, Any]:
            nonlocal max_prompt_tokens
            before = engine.get_stats().get("prompt_tokens", 0)
            response = original_generate(*args, **kwargs)
            after = engine.get_stats().get("prompt_tokens", 0)
            max_prompt_tokens = max(max_prompt_tokens, int(after) - int(before))
            return response

        engine.generate = measured_generate
        area_km2 = 4337.752  # externally supplied runtime guard, never included in the agent dataset/prompt
        agent = KeralaAgent(
            engine, question=question, arm=arm, data_text=build_data_text(), area_of_interest_km2=area_km2,
            pack=pack, timeout=int(config.get("sandbox_timeout", 300)), max_rounds=int(config.get("max_rounds", 12)),
            context_chars=int(config.get("context_chars", 24000)), verbose=False,
        )
        result = agent.run(compose_task(question, arm, pack=pack), data_dir=str(LAYERS), work_dir=str(out), on_step=events.append)
    except Exception as exc:
        caught = f"{type(exc).__name__}: {exc}"
    finally:
        (out / "trace.jsonl").write_text("".join(json.dumps(event, ensure_ascii=False) + "\n" for event in events), encoding="utf-8")
        for required_log in ("pack_calls.jsonl", "checker.jsonl"):
            (out / required_log).touch(exist_ok=True)
    _copy_required_outputs(out)
    elapsed = time.monotonic() - started
    stats = engine.get_stats()
    text = caught + "\n" + "\n".join(json.dumps(event) for event in events)
    if "429" in text or "RESOURCE_EXHAUSTED" in text:
        reason = "paused_quota"
    elif caught:
        reason = "error"
    elif result is not None and result.total_rounds >= int(config.get("max_rounds", 12)) and not result.success:
        reason = "max_rounds"
    else:
        reason = "finished"
    meta = {
        "model_id": config.get("model"), "model_name": model,
        "model_digest": _ollama_digest(config) if config.get("provider") == "ollama" else config.get("model"),
        "arm": arm, "qid": qid, "rounds": getattr(result, "total_rounds", 0),
        "llm_calls": stats.get("total_calls", 0), "prompt_tokens": stats.get("prompt_tokens", 0),
        "completion_tokens": stats.get("total_output_tokens", 0), "max_prompt_tokens": max_prompt_tokens,
        "wall_seconds": round(elapsed, 3), "backoff_seconds": float(getattr(engine, "backoff_seconds", 0.0)),
        "exit_reason": reason, "error": caught or None, "git_commit": _git_commit(),
        "pack_hash": _sha256(ROOT / "kerala" / "pack" / "kerala_pack.yaml"),
    }
    (out / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return meta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qid", required=True)
    parser.add_argument("--arm", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--stub-mode", choices=("ok", "quota", "sleep"), default="ok", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    print(json.dumps(run_one(args.qid, args.arm, args.model, args.out, stub_mode=args.stub_mode), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
