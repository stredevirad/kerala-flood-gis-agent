# SPDX-License-Identifier: AGPL-3.0-or-later
"""Re-label historical `paused_quota` runs with the F7 structured classifier.

Older runs were labelled by searching the whole trace for "429", which matched
digits inside `gen_time_ms`. This tool re-derives the label from structured
fields only (recorded error, quota counter, rounds, success) and keeps the
original label in `exit_reason_original` so the change stays auditable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from kerala.bench.run_one import classify_exit
from kerala.config import ROOT, model_config


EMERGENCY = {"emergency_plot.png", "emergency_output.geojson", "emergency_output.csv"}


def _success(run: Path) -> bool:
    """Mirror GISReActAgent: finished with outputs, or ran out of rounds with real outputs."""
    pred = run / "pred_results"
    real = [p for p in pred.iterdir() if not p.name.startswith(".") and p.name not in EMERGENCY] if pred.is_dir() else []
    return bool(real)


def relabel(batch_root: Path, apply: bool) -> list[tuple[Path, str, str]]:
    changes = []
    for meta_path in sorted(batch_root.rglob("meta.json")):
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("exit_reason") != "paused_quota":
            continue
        if meta.get("error"):
            continue  # a recorded exception needs a human look; leave it alone
        max_rounds = int(model_config(meta["model_name"]).get("max_rounds", 16))
        new = classify_exit(
            last_error=meta.get("last_api_error"), exception=None,
            rounds=int(meta.get("rounds", 0) or 0), success=_success(meta_path.parent), max_rounds=max_rounds,
        )
        if new == "paused_quota":
            continue
        changes.append((meta_path.parent, "paused_quota", new))
        if apply:
            meta["exit_reason_original"] = "paused_quota"
            meta["exit_reason"] = new
            meta["relabel_note"] = (
                "F7: original label came from a '429' substring inside gen_time_ms; "
                "no error, zero backoff, HTTP 200. Re-derived from structured fields."
            )
            meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=ROOT / "results" / "runs")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    for path, old, new in relabel(args.runs, args.apply):
        print(f"{'relabelled' if args.apply else 'would relabel'} {path.relative_to(ROOT)}: {old} -> {new}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
