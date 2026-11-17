# SPDX-License-Identifier: AGPL-3.0-or-later
"""Phase 6 analyses across matrix repeats.

(a) P01 method analysis: does a failed P01 answer equal the independent gold
    under a different facility rule (`intersects` = whole geometry, or
    `centroid`)? Matches are labelled PARAM_IGNORED when the rule was given
    (inline/pack) and PARAM_CHOICE when the model chose it (noparam).
(b) Run-to-run agreement of `correct_final` per cell (repeat 1 vs repeat 2),
    by arm, with Cohen's kappa.

Writes `analysis.md`/CSVs into the summary folder and appends the same tables
to `results_tables.md`, so every reported number is traceable.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from kerala.bench.gold import gold_fn
from kerala.config import ROOT

PACK_BUFFER_M = 250.0
SECTION = "## Analyses across repeats"


def _bool(value: Any) -> bool:
    return value is True or str(value) == "True"


def _read_rows(summary: Path) -> list[dict[str, Any]]:
    with (summary / "per_run.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def _answer_value(row: dict[str, Any]) -> Any:
    path = ROOT / "results" / "runs" / row["batch"] / row["model"] / row["qid"] / row["arm"] / "answer.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("value")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def _own_buffer(row: dict[str, Any]) -> float | None:
    try:
        value = json.loads(row["params_reported"]).get("facility_flood_buffer_m")
        return float(value) if value is not None else None
    except (ValueError, TypeError, json.JSONDecodeError, AttributeError):
        return None


def p01_method(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    cache: dict[tuple[str, float], Any] = {}

    def gold(rule: str, buffer_m: float) -> Any:
        key = (rule, buffer_m)
        if key not in cache:
            cache[key] = gold_fn("P01", {"facility_point_rule": rule, "facility_flood_buffer_m": buffer_m})["value"]
        return cache[key]

    detail = []
    for row in rows:
        if row["qid"] != "P01" or _bool(row["correct_final"]):
            continue
        value = _answer_value(row)
        buffers = {PACK_BUFFER_M}
        own = _own_buffer(row)
        if row["arm"] == "noparam" and own is not None and 0 < own <= 5000:
            buffers.add(own)
        match = ""
        for buffer_m in sorted(buffers):
            for rule in ("intersects", "centroid"):
                if isinstance(value, (int, float)) and not isinstance(value, bool) and value == gold(rule, buffer_m):
                    match = match or f"{rule} @ {buffer_m:g} m"
        label = ("PARAM_IGNORED" if row["arm"] in {"inline", "pack"} else "PARAM_CHOICE") if match else ""
        detail.append({"batch": row["batch"], "arm": row["arm"], "value": value, "matches": match, "label": label})
    counts = []
    for arm in ("noparam", "inline", "pack"):
        failed = [d for d in detail if d["arm"] == arm]
        counts.append({"arm": arm, "failed_runs": len(failed),
                       "PARAM_IGNORED": sum(d["label"] == "PARAM_IGNORED" for d in failed),
                       "PARAM_CHOICE": sum(d["label"] == "PARAM_CHOICE" for d in failed),
                       "no_rule_match": sum(not d["label"] for d in failed)})
    reference = [{"rule": rule, "buffer_m": b, "P01": v} for (rule, b), v in sorted(cache.items())]
    reference.append({"rule": "representative_point (gold)", "buffer_m": PACK_BUFFER_M, "P01": gold_fn("P01")["value"]})
    return detail, counts + [{"_reference": reference}]


def _kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    n = len(pairs)
    if not n:
        return None
    observed = sum(a == b for a, b in pairs) / n
    p1 = sum(a for a, _ in pairs) / n
    p2 = sum(b for _, b in pairs) / n
    expected = p1 * p2 + (1 - p1) * (1 - p2)
    return None if math.isclose(expected, 1.0) else (observed - expected) / (1 - expected)


def agreement(rows: list[dict[str, Any]], first: str, second: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by = {(r["batch"], r["model"], r["qid"], r["arm"]): r for r in rows}
    cells = []
    for (batch, model, qid, arm), row in sorted(by.items()):
        if batch != first or (second, model, qid, arm) not in by:
            continue
        other = by[(second, model, qid, arm)]
        a, b = _bool(row["correct_final"]), _bool(other["correct_final"])
        cells.append({"model": model, "qid": qid, "arm": arm, "r1_correct": a, "r2_correct": b,
                      "agree": a == b, "r1_exit": row["exit_reason"], "r2_exit": other["exit_reason"]})
    summary = []
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        groups[cell["arm"]].append(cell)
        groups["all"].append(cell)
    for arm in ("noparam", "inline", "pack", "all"):
        group = groups.get(arm, [])
        pairs = [(c["r1_correct"], c["r2_correct"]) for c in group]
        kappa = _kappa(pairs)
        summary.append({"arm": arm, "cells": len(group), "agree": sum(c["agree"] for c in group),
                        "both_right": sum(a and b for a, b in pairs), "both_wrong": sum(not a and not b for a, b in pairs),
                        "r1_only": sum(a and not b for a, b in pairs), "r2_only": sum(b and not a for a, b in pairs),
                        "agreement": round(sum(c["agree"] for c in group) / len(group), 3) if group else None,
                        "kappa": round(kappa, 3) if kappa is not None else None})
    return cells, summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, default=ROOT / "results" / "summary")
    parser.add_argument("--first", required=True)
    parser.add_argument("--second", required=True)
    args = parser.parse_args(argv)
    summary = args.summary if args.summary.is_absolute() else ROOT / args.summary
    rows = _read_rows(summary)
    detail, counts = p01_method(rows)
    reference = counts.pop()["_reference"]
    cells, agree = agreement(rows, args.first, args.second)
    _write_csv(summary / "p01_method.csv", detail)
    _write_csv(summary / "agreement_cells.csv", cells)
    _write_csv(summary / "agreement.csv", agree)

    lines = [SECTION, "", f"Repeats: `{args.first}` (r1) and `{args.second}` (r2).", "",
             "### P01 gold under alternative facility rules", "", "| Rule | Buffer m | P01 count |", "|---|---:|---:|"]
    lines += [f"| {r['rule']} | {r['buffer_m']:g} | {r['P01']} |" for r in reference]
    lines += ["", "### P01 failed runs matching another facility rule, by arm", "",
              "| Arm | Failed P01 runs | PARAM_IGNORED | PARAM_CHOICE | No rule match |", "|---|---:|---:|---:|---:|"]
    lines += [f"| {c['arm']} | {c['failed_runs']} | {c['PARAM_IGNORED']} | {c['PARAM_CHOICE']} | {c['no_rule_match']} |" for c in counts]
    lines += ["", "### P01 failed runs (detail)", "", "| Repeat | Arm | Value | Matches | Label |", "|---|---|---:|---|---|"]
    lines += [f"| {d['batch']} | {d['arm']} | {d['value']} | {d['matches'] or '—'} | {d['label'] or '—'} |" for d in detail]
    lines += ["", "### Run-to-run agreement of correct_final (r1 vs r2)", "",
              "| Arm | Cells | Agree | Both right | Both wrong | Only r1 right | Only r2 right | Agreement | Cohen's kappa |",
              "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    lines += [f"| {a['arm']} | {a['cells']} | {a['agree']} | {a['both_right']} | {a['both_wrong']} | {a['r1_only']} | {a['r2_only']} | "
              f"{a['agreement']} | {a['kappa'] if a['kappa'] is not None else 'n/a'} |" for a in agree]
    lines += ["", "### Cells whose outcome changed between repeats", "", "| QID | Arm | r1 | r2 |", "|---|---|---|---|"]
    lines += [f"| {c['qid']} | {c['arm']} | {'right' if c['r1_correct'] else 'wrong'} ({c['r1_exit']}) | {'right' if c['r2_correct'] else 'wrong'} ({c['r2_exit']}) |"
              for c in cells if not c["agree"]] or ["| — | — | — | — |"]
    text = "\n".join(lines) + "\n"
    (summary / "analysis.md").write_text(text, encoding="utf-8")
    tables = summary / "results_tables.md"
    existing = tables.read_text(encoding="utf-8") if tables.is_file() else ""
    if SECTION in existing:
        existing = existing[:existing.index(SECTION)].rstrip() + "\n"
    tables.write_text(existing + "\n" + text, encoding="utf-8")
    print(text.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
