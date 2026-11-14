# SPDX-License-Identifier: AGPL-3.0-or-later
"""Schedule isolated KeralaFloodBench runs with frozen-layer guards."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from kerala.config import ROOT, model_config


BENCH = ROOT / "kerala" / "bench"
FROZEN = BENCH / "frozen.json"
LAYERS = ROOT / "data" / "kerala" / "layers"
QUESTIONS = BENCH / "questions.yaml"
RUNS_ROOT = ROOT / "results" / "runs"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_frozen_layers() -> None:
    """Fail closed if the approved layer listing, sizes, or hashes changed."""
    frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
    expected = frozen["layers"]
    actual_names = sorted(path.name for path in LAYERS.iterdir() if path.is_file())
    if actual_names != [entry["name"] for entry in expected]:
        raise RuntimeError("frozen layer directory listing changed")
    for entry in expected:
        path = LAYERS / entry["name"]
        if path.stat().st_size != entry["bytes"] or _sha256(path) != entry["sha256"]:
            raise RuntimeError(f"frozen layer changed: {entry['name']}")


def _question_entries(selected: str) -> list[dict[str, Any]]:
    entries = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    requested = [token.strip() for token in selected.split(",") if token.strip()]
    if not requested or requested == ["all"]:
        return entries
    found = {entry["id"]: entry for entry in entries}
    unknown = sorted(set(requested) - set(found))
    if unknown:
        raise ValueError(f"Unknown question IDs: {unknown}")
    return [found[qid] for qid in requested]


def _arms_for(question: dict[str, Any], requested: list[str]) -> list[str]:
    allowed = ["noparam", "inline", "pack"] if question["type"] == "parameter" else ["noparam", "pack"]
    arms = [arm for arm in requested if arm in allowed]
    if not arms:
        raise ValueError(f"No allowed arms selected for {question['id']}")
    return arms


def planned_runs(questions: str, arms: str) -> list[tuple[str, str]]:
    """Question-grouped, arm-order-rotated schedule."""
    selected_arms = [token.strip() for token in arms.split(",") if token.strip()]
    plan: list[tuple[str, str]] = []
    for index, question in enumerate(_question_entries(questions)):
        usable = _arms_for(question, selected_arms)
        rotated = usable[index % len(usable):] + usable[:index % len(usable)]
        plan.extend((question["id"], arm) for arm in rotated)
    return plan


def _run_path(batch: str, model: str, qid: str, arm: str) -> Path:
    return RUNS_ROOT / batch / model / qid / arm


def _should_skip(path: Path) -> bool:
    meta = path / "meta.json"
    if not meta.is_file():
        return False
    try:
        return json.loads(meta.read_text(encoding="utf-8")).get("exit_reason") in {"finished", "max_rounds", "timeout"}
    except json.JSONDecodeError:
        return False


def _timeout_meta(path: Path, qid: str, arm: str, model: str, wall: float) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "meta.json").write_text(json.dumps({
        "qid": qid, "arm": arm, "model_name": model, "wall_seconds": round(wall, 3),
        "backoff_seconds": 0.0, "exit_reason": "timeout", "rounds": 0, "llm_calls": 0,
        "prompt_tokens": 0, "completion_tokens": 0, "max_prompt_tokens": 0,
    }, indent=2) + "\n", encoding="utf-8")


def run_batch(model: str, batch: str, questions: str, arms: str, *, resume: bool = False, dry_run: bool = False, stub_mode: str = "ok") -> list[Path]:
    """Run the schedule serially; return the paths launched or planned."""
    config = model_config(model)
    plan = planned_runs(questions, arms)
    output_paths: list[Path] = []
    quota_streak = 0
    elapsed_samples: list[float] = []
    for index, (qid, arm) in enumerate(plan, 1):
        path = _run_path(batch, model, qid, arm)
        if resume and _should_skip(path):
            print(f"skip resumed {qid}/{arm}")
            continue
        verify_frozen_layers()
        output_paths.append(path)
        if dry_run:
            print(f"plan {index}/{len(plan)}: {qid}/{arm} -> {path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        command = [str(ROOT / ".venv" / "Scripts" / "python.exe"), "-m", "kerala.bench.run_one", "--qid", qid, "--arm", arm, "--model", model, "--out", str(path)]
        if model == "stub":
            command.extend(["--stub-mode", stub_mode])
        start = time.monotonic()
        flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        process = subprocess.Popen(command, cwd=ROOT, creationflags=flags)
        limit = float(config.get("wall_clock_seconds", 1500))
        while process.poll() is None:
            heartbeat = path / "heartbeat.json"
            extra = 0.0
            if heartbeat.is_file():
                try:
                    extra = float(json.loads(heartbeat.read_text(encoding="utf-8")).get("backoff_seconds", 0.0))
                except Exception:
                    extra = 0.0
            if time.monotonic() - start > limit + extra:
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], check=False, capture_output=True)
                _timeout_meta(path, qid, arm, model, time.monotonic() - start)
                break
            time.sleep(0.1)
        wall = time.monotonic() - start
        verify_frozen_layers()
        elapsed_samples.append(wall)
        meta_path = path / "meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.is_file() else {"exit_reason": "error"}
        quota_streak = quota_streak + 1 if meta.get("exit_reason") == "paused_quota" else 0
        remaining = len(plan) - index
        eta = (sum(elapsed_samples) / len(elapsed_samples) * remaining) if elapsed_samples else 0
        print(f"done {index}/{len(plan)} {qid}/{arm}: {meta.get('exit_reason')}; ETA {eta / 60:.1f} min")
        if model == "cloud-flashlite" and quota_streak >= 3:
            print("quota exhausted, resume tomorrow")
            break
        rpm = config.get("rpm_limit")
        if model == "cloud-flashlite" and rpm:
            time.sleep(max(0.0, 60.0 / float(rpm) - wall))
    return output_paths


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--questions", default="all")
    parser.add_argument("--arms", default="noparam,inline,pack")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--stub-mode", choices=("ok", "quota", "sleep"), default="ok", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    run_batch(args.model, args.batch, args.questions, args.arms, resume=args.resume, dry_run=args.dry_run, stub_mode=args.stub_mode)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
