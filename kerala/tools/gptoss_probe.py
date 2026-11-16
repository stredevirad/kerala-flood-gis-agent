# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnose the gpt-oss response format through OpenAIEngine's client.

Sends the real D01/pack system prompt and task as one chat call per variant and
saves every full raw response, so content vs reasoning fields, finish_reason and
token counts can be inspected. Diagnostic only; never used for scoring.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from kerala.agent import build_data_text, build_system_prompt, compose_task
from kerala.config import ROOT, model_config
from kerala.pack.pack import DOMAIN_PARAM_DESCRIPTION, load_pack
from src.agent.llm_engine import OpenAIEngine
from src.agent.tools import GISToolkit


VARIANTS = {
    # Exactly what the floor runs sent: max_tokens 4096 plus the ReAct stop list.
    "as_floor": {"max_tokens": 4096, "stop": ["Observation:", "\nUser:"]},
    "no_stop": {"max_tokens": 4096},
    "low_effort_with_stop": {"max_tokens": 8192, "stop": ["Observation:", "\nUser:"], "reasoning_effort": "low"},
    "low_effort_no_stop": {"max_tokens": 8192, "reasoning_effort": "low"},
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="pc-gptoss20b")
    parser.add_argument("--variants", default=",".join(VARIANTS))
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "_profile" / "gptoss_raw.json")
    args = parser.parse_args(argv)

    config = model_config(args.model)
    pack = load_pack()
    import yaml
    questions = {q["id"]: q for q in yaml.safe_load((ROOT / "kerala" / "bench" / "questions.yaml").read_text(encoding="utf-8"))["questions"]}
    question = questions["D01"]
    toolkit = GISToolkit(sandbox=None, data_dir="dataset")
    system_prompt = build_system_prompt(
        tool_descriptions=toolkit.tool_descriptions + DOMAIN_PARAM_DESCRIPTION,
        arm="pack", needs_params=question.get("needs_params", []), data_text=build_data_text(), pack=pack,
    )
    task = compose_task(question, "pack", pack=pack)
    engine = OpenAIEngine(model=str(config["model"]), api_key="ollama", base_url=str(config["base_url"]),
                          temperature=0, max_tokens=4096, seed=config.get("seed"), request_timeout=900)
    if not engine.load_model():
        raise SystemExit("client init failed")

    results = {"model": config["model"], "question": "D01", "arm": "pack", "variants": {}}
    for name in [v.strip() for v in args.variants.split(",") if v.strip()]:
        extra = dict(VARIANTS[name])
        kwargs = {"model": config["model"], "temperature": 0, "seed": config.get("seed"),
                  "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": task}]}
        kwargs.update(extra)
        started = time.time()
        try:
            response = engine.client.chat.completions.create(**kwargs)
            raw = response.model_dump()
            message = raw["choices"][0]["message"]
            summary = {
                "finish_reason": raw["choices"][0].get("finish_reason"),
                "content_chars": len(message.get("content") or ""),
                "reasoning_chars": len(message.get("reasoning") or message.get("reasoning_content") or ""),
                "message_keys": sorted(message),
                "usage": raw.get("usage"),
            }
        except Exception as exc:  # record API rejections of a parameter as data
            raw, summary = None, {"error": f"{type(exc).__name__}: {exc}"}
        summary["seconds"] = round(time.time() - started, 1)
        summary["request_extra"] = extra
        results["variants"][name] = {"summary": summary, "raw": raw}
        print(name, json.dumps(summary), flush=True)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
