# SPDX-License-Identifier: AGPL-3.0-or-later
"""Floor-check diagnostics: one table of every floor run, value vs gold.

Uses the scorer's own `collect()` for format/correctness, then adds the reported
value, the frozen gold value, `parameters_used`, and the first failed step of
the trace. With `--p01-variants` it also evaluates the independent gold function
for P01 under other facility rules and buffers, to tell a method choice (the
model used a different rule or distance) from an execution error.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from kerala.bench.gold import gold_fn
from kerala.bench.score import RUNS_ROOT, collect
from kerala.config import ROOT


def _first_error(run: Path) -> str:
    trace = run / "trace.jsonl"
    if not trace.is_file():
        return "no trace"
    for line in trace.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("success") is False:
            text = str(event.get("observation_full") or event.get("observation") or "")
            lines = [s.strip() for s in text.splitlines() if s.strip() and not s.strip().startswith("[")]
            detail = next((s for s in lines if "Error" in s or "error" in s or "❌" in s), lines[0] if lines else "")
            return f"r{event.get('round')} `{event.get('action')}`: {detail[:110]}"
    return "—"


def _answer(run: Path) -> dict[str, Any]:
    path = run / "answer.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {"value": "unreadable"}


def rows_for(batch: str) -> list[dict[str, Any]]:
    out = []
    golds: dict[str, Any] = {}
    for row in collect(batch):
        run = RUNS_ROOT / row["batch"] / row["model"] / row["qid"] / row["arm"]
        answer = _answer(run)
        qid = row["qid"]
        if qid not in golds:
            golds[qid] = gold_fn(qid)["value"]
        out.append({
            "model": row["model"], "qid": qid, "arm": row["arm"], "exit_reason": row["exit_reason"],
            "format_ok": row["format_ok"], "correct_final": row["correct_final"],
            "correct_given_own_params": row["correct_given_own_params"],
            "value": answer.get("value"), "gold": golds[qid],
            "parameters_used": answer.get("parameters_used"), "first_error": _first_error(run),
            "rounds": json.loads((run / "meta.json").read_text(encoding="utf-8")).get("rounds") if (run / "meta.json").is_file() else None,
        })
    return out


def _yn(value: Any) -> str:
    if value is None or value == "":
        return "n/a"
    return "yes" if value is True or value == "True" else ("no" if value in (False, "False") else str(value))


def markdown(rows: list[dict[str, Any]]) -> str:
    head = ("| Model | QID / arm | exit_reason | format_ok | correct_final | correct_given_own_params | value vs gold | parameters_used | first error |\n"
            "|---|---|---|---:|---:|---:|---|---|---|")
    body = []
    for r in rows:
        params = json.dumps(r["parameters_used"], ensure_ascii=False) if r["parameters_used"] else "—"
        value = "—" if r["value"] is None else r["value"]
        body.append(f"| {r['model']} | {r['qid']} / {r['arm']} | {r['exit_reason']} | {_yn(r['format_ok'])} | {_yn(r['correct_final'])} | "
                    f"{_yn(r['correct_given_own_params'])} | {value} vs {r['gold']} | {params} | {r['first_error']} |")
    return head + "\n" + "\n".join(body)


def p01_variants() -> list[tuple[str, float, Any]]:
    results = []
    for rule in ("representative_point", "centroid", "intersects"):
        for buffer_m in (250, 500):
            value = gold_fn("P01", {"facility_point_rule": rule, "facility_flood_buffer_m": buffer_m})["value"]
            results.append((rule, buffer_m, value))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batches", required=True, help="comma-separated batch names")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "summary" / "floor_diagnostics.md")
    parser.add_argument("--p01-variants", action="store_true")
    args = parser.parse_args(argv)
    rows: list[dict[str, Any]] = []
    for batch in [b.strip() for b in args.batches.split(",") if b.strip()]:
        rows.extend(rows_for(batch))
    text = "# Floor-check diagnostics\n\n" + markdown(rows) + "\n"
    if args.p01_variants:
        text += "\n## P01 gold under alternative facility rules (independent gold function)\n\n| facility_point_rule | buffer m | P01 count |\n|---|---:|---:|\n"
        text += "\n".join(f"| {rule} | {b} | {v} |" for rule, b, v in p01_variants()) + "\n"
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    (args.out.with_suffix(".json")).write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
    print(text.encode("ascii", "replace").decode("ascii"))  # Windows consoles may be cp1252
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
