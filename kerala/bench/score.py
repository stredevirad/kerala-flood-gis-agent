# SPDX-License-Identifier: AGPL-3.0-or-later
"""Score Kerala benchmark runs without exposing gold data to agent workspaces."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import yaml

from kerala.bench.gold import gold_fn
from kerala.config import ROOT

matplotlib.use("Agg")
RUNS_ROOT = ROOT / "results" / "runs"
SUMMARY = ROOT / "results" / "summary"
QUESTIONS = ROOT / "kerala" / "bench" / "questions.yaml"
RUBRIC = ROOT / "kerala" / "bench" / "rubric.yaml"


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _answer(path: Path) -> dict[str, Any] | None:
    value = _read_json(path, None)
    return value if isinstance(value, dict) else None


def _normal_name(value: Any) -> str:
    return re.sub(r"[\W_]+", "", str(value).casefold().replace("taluk", ""))


def _is_correct(answer: dict[str, Any] | None, gold: dict[str, Any]) -> bool:
    if not answer or answer.get("status") != gold["status"] or answer.get("unit") != gold["unit"]:
        return False
    if gold["status"] == "cannot_answer":
        return answer.get("value") is None
    value = answer.get("value")
    if gold["unit"] == "count":
        return value == gold["value"]
    if gold["unit"] == "name":
        accepted = gold.get("tied") or [gold["value"]]
        return any(_normal_name(value) == _normal_name(name) for name in accepted)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    diff = abs(float(value) - float(gold["value"]))
    if gold["unit"] == "percent":
        return diff <= 1.0
    if gold["unit"] == "m":
        return diff <= 0.5
    return diff <= max(abs(float(gold["value"])) * 0.03, 1e-9)


def _defensible(params: dict[str, Any]) -> bool:
    ranges = yaml.safe_load(RUBRIC.read_text(encoding="utf-8"))["defensible_ranges"]
    for key, value in params.items():
        if key not in ranges:
            continue
        rule = ranges[key]
        if "allowed" in rule and value not in rule["allowed"]:
            return False
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        lower = rule.get("minimum", rule.get("minimum_months"))
        upper = rule.get("maximum", rule.get("maximum_months"))
        if lower is not None and not float(lower) <= numeric <= float(upper):
            return False
    return True


def _checker_rejections(path: Path) -> int:
    return sum(1 for record in (_read_json_line(line) for line in _lines(path)) if record and not record.get("accepted", False))


def _lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []


def _read_json_line(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _geo_flag(code: str) -> bool:
    loaded = re.search(r"(\w+)\s*=\s*(?:gpd\.)?read_file\([^\n]*(hospitals\.geojson|schools\.geojson)", code)
    if not loaded:
        return False
    variable = loaded.group(1)
    tail = code[loaded.end():]
    return bool(re.search(rf"\b{re.escape(variable)}\.(?:area|length|buffer|distance)\s*\(", tail) and not re.search(rf"\b{re.escape(variable)}\s*=\s*{re.escape(variable)}\.to_crs\(", tail))


def _taxonomy(row: dict[str, Any], trace: str) -> str:
    if row["correct_final"]:
        return ""
    reason = row["exit_reason"]
    if reason == "timeout":
        return "RATE_LIMIT" if row["backoff_seconds"] > row["wall_seconds"] * .5 else "TIMEOUT"
    if reason in {"error", "paused_quota"}:
        return "CRASH"
    if not row["format_ok"]:
        return "FORMAT"
    if "trimmed" in trace.casefold():
        return "CONTEXT"
    if row["expected_status"] == "cannot_answer" and row["answer_status"] == "ok":
        return "UNANSWERABLE_ANSWERED"
    if row["expected_status"] == "ok" and row["answer_status"] == "cannot_answer":
        return "REFUSED_ANSWERABLE"
    if row["geographic_measure_flag"] or "degrees" in row["checker_text"].casefold():
        return "CRS_UNIT"
    if row["arm"] == "noparam" and row["correct_given_own_params"]:
        return "PARAM_CHOICE"
    if "traceback" in trace.casefold() and "geoprocess" in trace.casefold():
        return "TOOL_BUG"
    return "LOGIC"


def collect(batch: str) -> list[dict[str, Any]]:
    question_map = {q["id"]: q for q in yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))["questions"]}
    rows: list[dict[str, Any]] = []
    root = RUNS_ROOT / batch
    for meta_path in sorted(root.glob("*/*/*/meta.json")):
        meta = _read_json(meta_path, {})
        run = meta_path.parent
        qid, arm, model = str(meta.get("qid", run.parent.name)), str(meta.get("arm", run.name)), str(meta.get("model_name", run.parents[2].name))
        question = question_map.get(qid)
        if not question:
            continue
        final = _answer(run / "answer.json")
        first = _answer(run / "attempts" / "answer_1.json")
        gold = gold_fn(qid)
        code = (run / "code.py").read_text(encoding="utf-8") if (run / "code.py").is_file() else ""
        trace = "\n".join(_lines(run / "trace.jsonl"))
        checker_text = "\n".join(_lines(run / "checker.jsonl"))
        params = final.get("parameters_used", {}) if final else {}
        own_correct = False
        defensible = _defensible(params) if isinstance(params, dict) and params else False
        if arm == "noparam" and defensible:
            try:
                own_correct = _is_correct(final, gold_fn(qid, params))
            except (KeyError, ValueError):
                own_correct = False
        row = {
            "batch": batch, "model": model, "qid": qid, "arm": arm, "expected_status": question["expected_status"],
            "format_ok": bool(final and set(final) == {"question_id", "status", "value", "unit", "parameters_used", "assumptions", "method"}),
            "correct_final": _is_correct(final, gold), "correct_first_attempt": _is_correct(first, gold),
            "checker_rejections": _checker_rejections(run / "checker.jsonl"), "pack_calls": len(_lines(run / "pack_calls.jsonl")),
            "params_reported": json.dumps(params, ensure_ascii=False, sort_keys=True),
            "params_in_code": bool(any(str(value) in code for value in params.values())) if isinstance(params, dict) else False,
            "geographic_measure_flag": _geo_flag(code), "assumption_stated": bool(final and str(final.get("assumptions", "")).strip()),
            "assumption_defensible": defensible, "correct_given_own_params": own_correct,
            "minutes": round(float(meta.get("wall_seconds", 0)) / 60, 4), "tokens": int(meta.get("prompt_tokens", 0)) + int(meta.get("completion_tokens", 0)),
            "exit_reason": meta.get("exit_reason", "error"), "backoff_seconds": float(meta.get("backoff_seconds", 0)), "wall_seconds": float(meta.get("wall_seconds", 0)),
            "answer_status": final.get("status") if final else "", "checker_text": checker_text,
        }
        row["taxonomy_auto"] = _taxonomy(row, trace)
        rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = fields or (list(rows[0]) if rows else [])
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows([{key: row.get(key, "") for key in keys} for row in rows])


def _figures(rows: list[dict[str, Any]]) -> None:
    arms = sorted({row["arm"] for row in rows}) or ["noparam", "inline", "pack"]
    values = [sum(bool(row["correct_final"]) for row in rows if row["arm"] == arm) / max(1, sum(row["arm"] == arm for row in rows)) for arm in arms]
    fig, ax = plt.subplots(); ax.bar(arms, values); ax.set_ylim(0, 1); ax.set_ylabel("accuracy"); fig.savefig(SUMMARY / "accuracy_by_arm.png", dpi=150); plt.close(fig)
    labels = sorted({row["taxonomy_auto"] for row in rows if row["taxonomy_auto"]}) or ["none"]
    fig, ax = plt.subplots(); bottom = [0] * len(arms)
    for label in labels:
        series = [sum(row["arm"] == arm and row["taxonomy_auto"] == label for row in rows) for arm in arms]
        ax.bar(arms, series, bottom=bottom, label=label); bottom = [a + b for a, b in zip(bottom, series)]
    ax.legend(fontsize=7); fig.savefig(SUMMARY / "taxonomy_by_arm.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(); ax.bar(arms, [sum(bool(r["correct_first_attempt"]) for r in rows if r["arm"] == a) for a in arms], label="first"); ax.bar(arms, [sum(bool(r["correct_final"]) for r in rows if r["arm"] == a) for a in arms], alpha=.6, label="final"); ax.legend(); fig.savefig(SUMMARY / "first_vs_final.png", dpi=150); plt.close(fig)
    sensitivity = json.loads((ROOT / "kerala" / "bench" / "gold_sensitivity.json").read_text(encoding="utf-8"))["answers"]
    fig, ax = plt.subplots()
    for qid in ("P05", "P06", "P03", "P09"):
        points = sensitivity.get(qid, {})
        xs = list(points); ys = [points[key]["value"] for key in xs]
        ax.plot(xs, ys, marker="o", label=qid)
    ax.legend(); ax.set_ylabel("gold value"); fig.savefig(SUMMARY / "sensitivity.png", dpi=150); plt.close(fig)


def score(batch: str) -> list[dict[str, Any]]:
    rows = collect(batch)
    SUMMARY.mkdir(parents=True, exist_ok=True)
    _write_csv(SUMMARY / "per_run.csv", rows)
    accuracy = []
    for key, group in _group(rows, lambda r: (r["qid"], r["arm"])):
        accuracy.append({"qid": key[0], "arm": key[1], "n": len(group), "accuracy": sum(bool(r["correct_final"]) for r in group) / len(group)})
    _write_csv(SUMMARY / "accuracy.csv", accuracy, ["qid", "arm", "n", "accuracy"])
    taxonomy = [{"batch": r["batch"], "model": r["model"], "qid": r["qid"], "arm": r["arm"], "taxonomy_auto": r["taxonomy_auto"], "manual_label": ""} for r in rows]
    _write_csv(SUMMARY / "taxonomy_auto.csv", taxonomy, ["batch", "model", "qid", "arm", "taxonomy_auto", "manual_label"])
    paired = _paired(rows)
    _write_csv(SUMMARY / "paired_tables.csv", paired, ["comparison", "both_right", "only_left", "only_right", "both_wrong", "descriptive_sign_test_p"])
    _figures(rows)
    table = ["# KeralaFloodBench results", "", "## Accuracy", "", "| QID | Arm | n | Accuracy |", "|---|---|---:|---:|"]
    table += [f"| {r['qid']} | {r['arm']} | {r['n']} | {r['accuracy']:.3f} |" for r in accuracy]
    table += ["", "## Paired comparisons", "", "| Comparison | Both right | Only left | Only right | Both wrong | Descriptive sign-test p |", "|---|---:|---:|---:|---:|---:|"]
    table += [f"| {r['comparison']} | {r['both_right']} | {r['only_left']} | {r['only_right']} | {r['both_wrong']} | {r['descriptive_sign_test_p']:.5f} |" for r in paired]
    (SUMMARY / "results_tables.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    return rows


def _group(rows: list[dict[str, Any]], keyfn):
    bucket: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for row in rows: bucket[keyfn(row)].append(row)
    return sorted(bucket.items())


def _paired(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by = {(r["model"], r["qid"], r["arm"]): r for r in rows}
    output = []
    for label, left, right, prefix in (("A3 vs A2", "pack", "inline", "P"), ("A2 vs A1", "inline", "noparam", "P"), ("A3 vs A1 controls", "pack", "noparam", "C")):
        pairs = [(a, b) for (model, qid, arm), a in by.items() if arm == left and qid.startswith(prefix) and (b := by.get((model, qid, right)))]
        both = sum(a["correct_final"] and b["correct_final"] for a,b in pairs); only_l = sum(a["correct_final"] and not b["correct_final"] for a,b in pairs); only_r = sum(not a["correct_final"] and b["correct_final"] for a,b in pairs); neither = len(pairs)-both-only_l-only_r
        n = only_l + only_r
        p = 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, k) for k in range(min(only_l, only_r) + 1)) / 2**n)
        output.append({"comparison": label, "both_right": both, "only_left": only_l, "only_right": only_r, "both_wrong": neither, "descriptive_sign_test_p": p})
    return output


def main(argv: list[str] | None = None) -> int:
    global SUMMARY
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--batch", required=True)
    parser.add_argument("--out", type=Path, default=None, help="summary directory (default results/summary)")
    args = parser.parse_args(argv)
    if args.out is not None:
        SUMMARY = args.out if args.out.is_absolute() else ROOT / args.out
    rows = score(args.batch); print(f"Scored {len(rows)} runs into {SUMMARY}"); return 0


if __name__ == "__main__": raise SystemExit(main())
