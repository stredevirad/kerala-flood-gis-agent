# SPDX-License-Identifier: AGPL-3.0-or-later
"""Compact digest of failed runs: actions, first errors, answer vs gold. Usage: python -m kerala.tools.failure_digest <batch> <summary_dir>"""
import csv, json, sys, collections
from pathlib import Path

batch = sys.argv[1]
summary = Path(sys.argv[2])
rows = list(csv.DictReader(open(summary / "per_run.csv", encoding="utf-8")))
gold = json.load(open("kerala/bench/gold.json", encoding="utf-8"))["answers"]
for r in rows:
    if r["correct_final"] == "True":
        continue
    run = Path("results/runs") / batch / r["model"] / r["qid"] / r["arm"]
    ev = [json.loads(l) for l in open(run / "trace.jsonl", encoding="utf-8")]
    acts = collections.Counter(e.get("action") for e in ev)
    fails = [e for e in ev if e.get("success") is False]
    errs = []
    for e in fails[:3]:
        obs = str(e.get("observation_full") or "")
        line = next((s.strip() for s in obs.splitlines() if ("Error" in s or "❌" in s or "error" in s) and s.strip()), obs[:80])
        errs.append(f"r{e.get('round')} {e.get('action')}: {line[:110]}")
    try:
        ans = json.load(open(run / "answer.json", encoding="utf-8"))
        val = (ans.get("status"), ans.get("value"))
    except Exception:
        val = "NO ANSWER"
    g = gold[r["qid"]]
    print(f"== {r['qid']}/{r['arm']} tax={r['taxonomy_auto']} exit={r['exit_reason']} rounds={len(ev)} packcalls={r['pack_calls']} ans={val} gold={(g['status'], g['value'])}")
    print("   actions:", dict(acts), "| last:", ev[-1].get("action") if ev else None)
    for x in errs:
        print("   ", x)
