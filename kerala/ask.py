# SPDX-License-Identifier: AGPL-3.0-or-later
"""Run a single ad-hoc Kerala question through the pack arm."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from kerala.bench.run_one import run_one
from kerala.config import ROOT


def _question_id(text: str) -> str:
    import yaml
    entries = yaml.safe_load((ROOT / "kerala" / "bench" / "questions.yaml").read_text(encoding="utf-8"))["questions"]
    normalized = text.strip().casefold()
    for entry in entries:
        if entry["text"].casefold() == normalized or entry["id"].casefold() == normalized:
            return entry["id"]
    raise ValueError("Demo question must exactly match a benchmark question or an ID")


def _map(path: Path) -> None:
    layers = ROOT / "data" / "kerala" / "layers"
    districts = gpd.read_file(layers / "districts.gpkg")
    fig, ax = plt.subplots(figsize=(7, 7))
    districts.boundary.plot(ax=ax, color="#202a44", linewidth=1.2)
    ax.set_axis_off(); ax.set_title("KeralaFloodBench demo area")
    fig.savefig(path / "map.png", dpi=150, bbox_inches="tight"); plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question"); parser.add_argument("--model", default="local-qwen7b")
    args = parser.parse_args(argv)
    qid = _question_id(args.question)
    out = ROOT / "results" / "demo" / time.strftime("%Y%m%d-%H%M%S")
    meta = run_one(qid, "pack", args.model, out)
    _map(out)
    print((out / "answer.json").read_text(encoding="utf-8") if (out / "answer.json").is_file() else "No answer.json")
    print((out / "pack_calls.jsonl").read_text(encoding="utf-8") if (out / "pack_calls.jsonl").is_file() else "No pack calls")
    print((out / "checker.jsonl").read_text(encoding="utf-8") if (out / "checker.jsonl").is_file() else "No checker log")
    print(json.dumps(meta, indent=2)); return 0


if __name__ == "__main__": raise SystemExit(main())
