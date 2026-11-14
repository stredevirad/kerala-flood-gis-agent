# GISclaw — an LLM agent for geospatial analysis.
# Copyright (C) 2026 Han Jinzhen
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Phase 0 local timing run for the GISclaw urban-heat example."""
import argparse
import ctypes
import json
import os
import threading
import time
from pathlib import Path

from src.agent.llm_engine import OpenAIEngine
from src.agent.react_agent import GISReActAgent


def peak_working_set_mb():
    """Return the process high-water working set on Windows."""
    from ctypes import wintypes

    class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
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
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    get_current_process = kernel32.GetCurrentProcess
    get_current_process.argtypes = []
    get_current_process.restype = wintypes.HANDLE
    get_process_memory_info = psapi.GetProcessMemoryInfo
    get_process_memory_info.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    ]
    get_process_memory_info.restype = wintypes.BOOL
    ok = get_process_memory_info(
        get_current_process(), ctypes.byref(counters), counters.cb
    )
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return round(counters.PeakWorkingSetSize / (1024 * 1024), 1)


def system_memory_used_gb():
    """Return current physical RAM use on Windows."""
    from ctypes import wintypes

    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [
            ("dwLength", wintypes.DWORD),
            ("dwMemoryLoad", wintypes.DWORD),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = MEMORYSTATUSEX()
    status.dwLength = ctypes.sizeof(status)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    global_memory_status = kernel32.GlobalMemoryStatusEx
    global_memory_status.argtypes = [ctypes.POINTER(MEMORYSTATUSEX)]
    global_memory_status.restype = wintypes.BOOL
    if not global_memory_status(ctypes.byref(status)):
        raise ctypes.WinError(ctypes.get_last_error())
    return (status.ullTotalPhys - status.ullAvailPhys) / (1024**3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="for example vulkan or cpu")
    parser.add_argument("--base-url", default="http://localhost:11434/v1")
    parser.add_argument("--model", default="gisclaw-qwen7b-16k")
    parser.add_argument("--out", default="logs/phase0_timing")
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

        peak_ram = [system_memory_used_gb()]
        stop_sampler = threading.Event()

        def sample_system_ram():
            while not stop_sampler.wait(0.5):
                peak_ram[0] = max(peak_ram[0], system_memory_used_gb())

        sampler = threading.Thread(target=sample_system_ram, daemon=True)
        sampler.start()
        start = time.perf_counter()
        try:
            result = agent.run(
                "Compute the mean temperature per block and save a choropleth PNG",
                data_dir="examples/urban-heat-madison",
                work_dir=str(out / "work"),
                on_step=on_step,
            )
        finally:
            stop_sampler.set()
            sampler.join()
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
        "peak_system_ram_used_gb": round(peak_ram[0], 2),
        "call_log": str(events_path),
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
