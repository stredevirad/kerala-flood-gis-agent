# SPDX-License-Identifier: AGPL-3.0-or-later
"""Failure report for one scored batch (local analysis only; no model calls).

Reads `per_run.csv` (written by `kerala.bench.score`) and each run's
`trace.jsonl`, `answer.json` and `meta.json`. It writes:

- per-arm results (accuracy, correct_given_own_params, exit reasons, the
  automatic taxonomy, cost);
- tool-protocol error counts over the incorrect runs (unknown geoprocess op,
  unexpected argument name, unknown tool, NameError inside geoprocess);
- domain_param calls in the pack arm;
- the first protocol error of every incorrect run, as a short excerpt with
  its run id.

Usage:
    .\\.venv\\Scripts\\python.exe -m kerala.tools.failure_report --batch matrix_gptoss_v1 --summary results\\summary\\matrix_gptoss_v1
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from kerala.config import ROOT

ARMS = ("noparam", "inline", "pack")
UNKNOWN_OP = re.compile(r"Unknown geoprocess op '(\w+)'")
UNEXPECTED_ARG = re.compile(r"Tool '(\w+)' argument error: [\w.]+\(\) got an unexpected keyword argument '(\w+)'")
UNKNOWN_TOOL = re.compile(r"Unknown tool '(\w+)'")
NAME_ERROR = re.compile(r"NameError: name '(\w+)' is not defined")


def _bool(value: Any) -> bool:
    return value is True or str(value) == "True"


def _events(run: Path) -> list[dict[str, Any]]:
    events = []
    for line in (run / "trace.jsonl").read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _answer(run: Path) -> dict[str, Any] | None:
    try:
        data = json.loads((run / "answer.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _clip(text: str, n: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _protocol_errors(event: dict[str, Any]) -> list[tuple[str, str]]:
    obs = str(event.get("observation_full") or event.get("observation") or "")
    found = [("unknown_geoprocess_op", m) for m in UNKNOWN_OP.findall(obs)]
    found += [("unexpected_argument", f"{tool}({arg}=)") for tool, arg in UNEXPECTED_ARG.findall(obs)]
    found += [("unknown_tool", m) for m in UNKNOWN_TOOL.findall(obs)]
    if event.get("action") == "geoprocess":
        found += [("geoprocess_nameerror", m) for m in NAME_ERROR.findall(obs)[:1]]
    return found


def _error_line(event: dict[str, Any]) -> str:
    """The line of the toolkit reply that carries the error, not the banner."""
    obs = str(event.get("observation_full") or event.get("observation") or "")
    for pattern in (UNKNOWN_OP, UNEXPECTED_ARG, UNKNOWN_TOOL, NAME_ERROR):
        match = pattern.search(obs)
        if match:
            start = obs.rfind("\n", 0, match.start()) + 1
            end = obs.find("\n", match.end())
            return obs[start:end if end != -1 else len(obs)]
    return obs.splitlines()[0] if obs else ""


def analyse(batch: str, summary: Path) -> dict[str, Any]:
    with (summary / "per_run.csv").open(encoding="utf-8", newline="") as stream:
        rows = [r for r in csv.DictReader(stream) if r["batch"] == batch]
    runs = []
    for row in rows:
        run_dir = ROOT / "results" / "runs" / row["batch"] / row["model"] / row["qid"] / row["arm"]
        events = _events(run_dir)
        answer = _answer(run_dir)
        meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
        errors = []
        first = None
        for event in events:
            found = _protocol_errors(event)
            errors += found
            if found and first is None:
                first = {
                    "round": event.get("round"),
                    "action": event.get("action"),
                    "args": _clip(event.get("args_summary", ""), 110),
                    "observation": _clip(_error_line(event), 120),
                    "error": f"{found[0][0]}: {found[0][1]}",
                }
        runs.append({
            "run_id": f"{row['batch']}/{row['qid']}/{row['arm']}",
            "qid": row["qid"], "arm": row["arm"],
            "correct": _bool(row["correct_final"]),
            "cgop": _bool(row["correct_given_own_params"]),
            "format_ok": _bool(row["format_ok"]),
            "exit": row["exit_reason"], "taxonomy": row["taxonomy_auto"],
            "pack_calls": int(row["pack_calls"] or 0),
            "rounds": meta.get("rounds"),
            "minutes": float(row["minutes"] or 0), "tokens": int(row["tokens"] or 0),
            "answer_written": answer is not None,
            "value": answer.get("value") if answer else None,
            "errors": errors, "first_error": first, "meta": meta,
            "actions": Counter(str(e.get("action")) for e in events),
        })
    return {"batch": batch, "runs": runs}


def render(result: dict[str, Any]) -> str:
    runs = result["runs"]
    wrong = [r for r in runs if not r["correct"]]
    lines = [f"# Failure report: `{result['batch']}`", "",
             "Generated by `kerala.tools.failure_report` from `per_run.csv` and the run traces (no model calls).", "",
             "## Per-arm results", "",
             "| Arm | Runs | Correct | Accuracy | correct_given_own_params | format_ok | finished | max_rounds | Minutes | Tokens | Minutes per correct |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for arm in ARMS:
        group = [r for r in runs if r["arm"] == arm]
        correct = sum(r["correct"] for r in group)
        minutes = sum(r["minutes"] for r in group)
        lines.append(
            f"| {arm} | {len(group)} | {correct} | {correct / len(group):.3f} | {sum(r['cgop'] for r in group)} | "
            f"{sum(r['format_ok'] for r in group)} | {sum(r['exit'] == 'finished' for r in group)} | "
            f"{sum(r['exit'] == 'max_rounds' for r in group)} | {minutes:.2f} | {sum(r['tokens'] for r in group)} | "
            f"{(minutes / correct) if correct else float('nan'):.2f} |")
    for label, keep in (("Parameter questions P01–P12", "P"), ("Controls C01–C08", "C")):
        lines += ["", f"### {label}", "", "| Arm | Runs | Correct |", "|---|---:|---:|"]
        for arm in ARMS:
            group = [r for r in runs if r["arm"] == arm and r["qid"].startswith(keep)]
            if group:
                lines.append(f"| {arm} | {len(group)} | {sum(r['correct'] for r in group)} |")
    total_correct = sum(r["correct"] for r in runs)
    metas = [r["meta"] for r in runs]

    def _num(key: str) -> list[float]:
        return [float(m[key]) for m in metas if isinstance(m.get(key), (int, float))]

    lines += ["", "### Run statistics (from meta.json)", "", "| Statistic | Value |", "|---|---:|",
              f"| exit_reason finished / max_rounds / other | {sum(m.get('exit_reason') == 'finished' for m in metas)} / "
              f"{sum(m.get('exit_reason') == 'max_rounds' for m in metas)} / "
              f"{sum(m.get('exit_reason') not in ('finished', 'max_rounds') for m in metas)} |",
              f"| Total wall time (h) | {sum(_num('wall_seconds')) / 3600:.2f} |",
              f"| Mean wall time per run (min) | {sum(_num('wall_seconds')) / 60 / max(len(metas), 1):.2f} |",
              f"| Total rounds | {sum(_num('rounds')):.0f} |",
              f"| Native tool calls rendered (F8) | {sum(_num('native_tool_calls')):.0f} |",
              f"| Raw-code tool calls recovered from Ollama 500 (F8) | {sum(_num('recovered_tool_calls')):.0f} |",
              f"| Largest per-call prompt (tokens) | {max(_num('max_prompt_tokens') or [0]):.0f} |",
              f"| Peak system RAM (GB) | {max(_num('peak_system_ram_gb') or [0]):.2f} |",
              f"| Peak VRAM used (MiB) | {max(_num('peak_vram_used_mib') or [0]):.0f} |",
              f"| Quota errors | {sum(_num('quota_errors')):.0f} |"]
    lines += ["", f"Total: {len(runs)} runs, {total_correct} correct, {len(wrong)} incorrect.", "",
              "## Automatic taxonomy of the incorrect runs (score.py labels), by arm", "",
              "| Label | noparam | inline | pack | All |", "|---|---:|---:|---:|---:|"]
    for label in sorted({r["taxonomy"] for r in wrong}):
        counts = [sum(r["arm"] == arm and r["taxonomy"] == label for r in wrong) for arm in ARMS]
        lines.append(f"| {label} | {' | '.join(map(str, counts))} | {sum(counts)} |")

    kinds = ("unknown_geoprocess_op", "unexpected_argument", "unknown_tool", "geoprocess_nameerror")
    lines += ["", "## Tool-protocol errors in the incorrect runs", "",
              "A tool-protocol error is a call the toolkit rejects before any GIS runs: an op name that `geoprocess` does not have, "
              "an argument name the tool does not accept, a tool that does not exist, or a `geoprocess` call that refers to a variable never created.", "",
              "| Error kind | Events | Incorrect runs with ≥ 1 |", "|---|---:|---:|"]
    for kind in kinds:
        lines.append(f"| {kind} | {sum(1 for r in wrong for k, _ in r['errors'] if k == kind)} | "
                     f"{sum(any(k == kind for k, _ in r['errors']) for r in wrong)} |")
    any_err = [r for r in wrong if r["errors"]]
    strict = [r for r in wrong if any(k != "geoprocess_nameerror" for k, _ in r["errors"])]
    no_answer = [r for r in wrong if not r["answer_written"]]
    lines += ["", f"- Incorrect runs with at least one tool-protocol error: **{len(any_err)} of {len(wrong)}**.",
              f"- Incorrect runs with an unknown op, unexpected argument or unknown tool (not counting NameError): **{len(strict)} of {len(wrong)}**.",
              f"- Correct runs with at least one tool-protocol error: {sum(bool(r['errors']) for r in runs if r['correct'])} of {total_correct}.",
              f"- Incorrect runs that never wrote `answer.json`: **{len(no_answer)}**; of these, {sum(bool(r['errors']) for r in no_answer)} had a tool-protocol error.",
              "", "### Most frequent offending names", "", "| Error kind | Name | Events |", "|---|---|---:|"]
    named = Counter((k, v) for r in wrong for k, v in r["errors"])
    lines += [f"| {k} | `{v}` | {n} |" for (k, v), n in named.most_common(15)]

    pack = [r for r in runs if r["arm"] == "pack"]
    lines += ["", "## domain_param calls in the pack arm", "", "| Run | Correct | domain_param calls |", "|---|---|---:|"]
    lines += [f"| {r['run_id']} | {'yes' if r['correct'] else 'no'} | {r['pack_calls']} |" for r in pack]
    p_pack = [r for r in pack if r["qid"].startswith("P")]
    zero = [r for r in pack if r["pack_calls"] == 0]
    lines += ["", f"- Parameter questions in the pack arm that called `domain_param`: {sum(r['pack_calls'] > 0 for r in p_pack)} of {len(p_pack)}.",
              f"- Pack runs with zero `domain_param` calls: {len(zero)} ({', '.join(r['qid'] for r in zero) or 'none'}); "
              f"{sum(r['correct'] for r in zero)} of them correct."]

    first_kinds = Counter(r["first_error"]["error"].split(":")[0] if r["first_error"] else "none" for r in wrong)
    lines += ["", "### Kind of the first tool-protocol error, incorrect runs", "", "| Kind | Runs |", "|---|---:|"]
    lines += [f"| {k} | {n} |" for k, n in first_kinds.most_common()]
    lines += ["", "## First tool-protocol error of each incorrect run", "",
              "| Run | Exit | Answer written | Round | Action | Arguments (excerpt) | Toolkit reply (excerpt) |",
              "|---|---|---|---:|---|---|---|"]
    for r in wrong:
        f = r["first_error"]
        if f:
            lines.append(f"| {r['run_id']} | {r['exit']} | {'yes' if r['answer_written'] else 'no'} | {f['round']} | `{f['action']}` | "
                         f"`{f['args'].replace('|', '/')}` | {f['observation'].replace('|', '/')} |")
        else:
            lines.append(f"| {r['run_id']} | {r['exit']} | {'yes' if r['answer_written'] else 'no'} | — | — | (no tool-protocol error) | — |")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = args.summary if args.summary.is_absolute() else ROOT / args.summary
    result = analyse(args.batch, summary)
    text = render(result)
    (summary / "failure_report.md").write_text(text, encoding="utf-8")
    with (summary / "failure_runs.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["run_id", "qid", "arm", "correct", "exit", "taxonomy", "answer_written", "value",
                         "pack_calls", "protocol_errors", "first_error"])
        for r in result["runs"]:
            writer.writerow([r["run_id"], r["qid"], r["arm"], r["correct"], r["exit"], r["taxonomy"], r["answer_written"],
                             r["value"], r["pack_calls"], len(r["errors"]), (r["first_error"] or {}).get("error", "")])
    print(text.encode("ascii", "replace").decode("ascii"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
