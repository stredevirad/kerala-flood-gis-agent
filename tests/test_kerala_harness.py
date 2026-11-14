# SPDX-License-Identifier: AGPL-3.0-or-later
"""Offline coverage for the Kerala subprocess harness and scorer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kerala.bench import run_bench
from kerala.bench.run_one import run_one
from kerala.bench.score import score


def test_stub_run_one_writes_required_bundle(tmp_path):
    out = tmp_path / "one"
    meta = run_one("D01", "pack", "stub", out)
    assert meta["exit_reason"] == "finished"
    for name in ("answer.json", "attempts", "code.py", "trace.jsonl", "pack_calls.jsonl", "checker.jsonl", "meta.json"):
        assert (out / name).exists()


def test_run_bench_end_to_end_and_resume(monkeypatch, tmp_path):
    root = tmp_path / "runs"
    monkeypatch.setattr(run_bench, "ROOT", tmp_path)
    monkeypatch.setattr(run_bench, "RUNS_ROOT", root)
    monkeypatch.setattr(run_bench, "verify_frozen_layers", lambda: None)
    monkeypatch.setattr(run_bench, "planned_runs", lambda *_: [("D01", "pack")])
    path = root / "batch" / "stub" / "D01" / "pack"
    path.mkdir(parents=True)
    (path / "meta.json").write_text(json.dumps({"exit_reason": "finished"}), encoding="utf-8")
    result = run_bench.run_batch("stub", "batch", "D01", "pack", resume=True, dry_run=True)
    assert result == []


def test_timeout_kill_writes_timeout_meta(monkeypatch, tmp_path):
    root = tmp_path / "runs"
    monkeypatch.setattr(run_bench, "ROOT", tmp_path)
    monkeypatch.setattr(run_bench, "RUNS_ROOT", root)
    monkeypatch.setattr(run_bench, "verify_frozen_layers", lambda: None)
    monkeypatch.setattr(run_bench, "planned_runs", lambda *_: [("D01", "pack")])
    monkeypatch.setattr(run_bench, "model_config", lambda _name: {"wall_clock_seconds": 0.0})

    class Slow:
        pid = 99
        def poll(self): return None
    monkeypatch.setattr(run_bench.subprocess, "Popen", lambda *a, **k: Slow())
    monkeypatch.setattr(run_bench.subprocess, "run", lambda *a, **k: None)
    run_bench.run_batch("stub", "timeout", "D01", "pack")
    meta = json.loads((root / "timeout" / "stub" / "D01" / "pack" / "meta.json").read_text(encoding="utf-8"))
    assert meta["exit_reason"] == "timeout"


def test_paused_quota_is_not_resume_skippable(tmp_path):
    path = tmp_path / "quota"
    path.mkdir()
    (path / "meta.json").write_text(json.dumps({"exit_reason": "paused_quota"}), encoding="utf-8")
    assert not run_bench._should_skip(path)


def test_frozen_hash_change_aborts_batch(monkeypatch, tmp_path):
    layers = tmp_path / "layers"; layers.mkdir()
    file = layers / "x.txt"; file.write_text("one", encoding="utf-8")
    frozen = tmp_path / "frozen.json"
    frozen.write_text(json.dumps({"layers": [{"name": "x.txt", "bytes": 3, "sha256": run_bench._sha256(file)}]}), encoding="utf-8")
    monkeypatch.setattr(run_bench, "LAYERS", layers); monkeypatch.setattr(run_bench, "FROZEN", frozen)
    run_bench.verify_frozen_layers()
    file.write_text("two", encoding="utf-8")
    with pytest.raises(RuntimeError, match="frozen layer changed"):
        run_bench.verify_frozen_layers()


def test_score_produces_every_required_output(monkeypatch, tmp_path):
    import kerala.bench.score as scoring
    monkeypatch.setattr(scoring, "SUMMARY", tmp_path / "summary")
    monkeypatch.setattr(scoring, "collect", lambda _batch: [])
    score("empty")
    for name in ("per_run.csv", "accuracy.csv", "paired_tables.csv", "taxonomy_auto.csv", "results_tables.md", "accuracy_by_arm.png", "taxonomy_by_arm.png", "first_vs_final.png", "sensitivity.png"):
        assert (tmp_path / "summary" / name).is_file()
