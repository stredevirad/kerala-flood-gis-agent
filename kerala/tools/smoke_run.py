# GISclaw — an LLM agent for geospatial analysis.
# Copyright (C) 2026 Han Jinzhen
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Phase 0 local timing run for the GISclaw urban-heat example."""
import argparse
import ctypes
import json
import os
import time
from pathlib import Path

from src.agent.llm_engine import OpenAIEngine
from src.agent.react_agent import GISReActAgent


def peak_working_set_mb():
    """Return the process high-water working set on Windows."""
    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    counters = PROCESS_MEMORY_COUNTERS()
    counters.cb = ctypes.sizeof(counters)
    process = ctypes.windll.kernel32.GetCurrentProcess()
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(
        process, ctypes.byref(counters), counters.cb
    )
    if not ok:
        raise ctypes.WinError()
    return round(counters.PeakWorkingSetSize / (1024 * 1024), 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="for example vulkan or cpu")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--model", default="gisclaw-qwen7b-16k")
    parser.add_argument("--out", default="results/phase0_timing")
    args = parser.parse_args()

    out = Path(args.out) / args.label
    out.mkdir(parents=True, exist_ok=True)
    engine = OpenAIEngine(model=args.model, api_key="ollama", temperature=0,
                          max_tokens=1536, base_url=args.base_url)
    if not engine.load_model():
        raise SystemExit("Could not initialize the OpenAI-compatible Ollama client")

    agent = GISReActAgent(engine, timeout=300, max_rounds=12, verbose=True,
                          context_chars=24000)
    last = {"calls": 0, "prompt": 0, "completion": 0}
    events_path = out / "calls.jsonl"
    with events_path.open("w", encoding="utf-8") as events:
        def on_step(event):
            stats = engine.get_stats()
            calls = stats["total_calls"]
            record = {
                "round": event.get("round"),
                "action": event.get("action"),
                "wall_seconds": round(event.get("gen_time_ms", 0) / 1000, 3),
                "prompt_tokens": stats["prompt_tokens"] - last["prompt"],
                "completion_tokens": stats["total_output_tokens"] - last["completion"],
                "llm_call": calls - last["calls"],
            }
            events.write(json.dumps(record, ensure_ascii=False) + "\n")
            events.flush()
            last.update(calls=calls, prompt=stats["prompt_tokens"],
                        completion=stats["total_output_tokens"])

        start = time.perf_counter()
        result = agent.run(
            "Compute the mean temperature per block and save a choropleth PNG",
            data_dir="examples/urban-heat-madison",
            work_dir=str(out / "work"),
            on_step=on_step,
        )
        wall = time.perf_counter() - start

    stats = engine.get_stats()
    summary = {
        "label": args.label,
        "backend": os.environ.get("OLLAMA_VULKAN", "default; verify from server log"),
        "success": result.success,
        "rounds": result.total_rounds,
        "wall_seconds": round(wall, 2),
        "minutes_per_run": round(wall / 60, 2),
        "calls": stats["total_calls"],
        "mean_seconds_per_call": round(wall / max(stats["total_calls"], 1), 2),
        "prompt_tokens": stats["prompt_tokens"],
        "completion_tokens": stats["total_output_tokens"],
        "peak_working_set_mb": peak_working_set_mb(),
        "call_log": str(events_path),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
