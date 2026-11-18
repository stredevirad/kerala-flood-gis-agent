# SPDX-License-Identifier: AGPL-3.0-or-later
"""Render one run's trace.jsonl as a self-contained HTML page (standard library only).

Usage:
    .venv/Scripts/python.exe -m kerala.bench.trace_html results/runs/<batch>/<model>/<qid>/<arm> [--out page.html]

The page shows each round's thought, action, arguments or code, observation and
success flag, plus the run's meta.json and final answer. Raw model replies
(`raw_replies`, logged from repeat 2 onwards) are shown in collapsed blocks.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#e4e1d8;--ok:#1f7a4d;--bad:#b42318;--code:#f3f1ea}
@media (prefers-color-scheme: dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a29b;--card:#1f1f1c;--line:#34332e;--ok:#4cc38a;--bad:#ff7b72;--code:#262622}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 16px}
h1{font-size:20px;margin:0 0 4px} .muted{color:var(--muted)}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:12px 0}
.ok{color:var(--ok)} .bad{color:var(--bad)}
pre{background:var(--code);padding:10px;border-radius:6px;overflow-x:auto;white-space:pre-wrap;word-break:break-word;font-size:13px}
summary{cursor:pointer;color:var(--muted)} table{border-collapse:collapse} td{padding:2px 10px 2px 0;vertical-align:top}
"""


def _pre(value: Any) -> str:
    text = value if isinstance(value, str) else json.dumps(value, indent=2, ensure_ascii=False)
    return f"<pre>{html.escape(text)}</pre>"


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# Absolute Windows paths recorded on the machine that ran the agent, in single- or
# double-backslash (JSON/repr) form. Paths inside a checkout of this repo become
# repo-relative; any other path under a user profile keeps only "<user-home>".
_SEP = r"(?:\\{1,2}|/)"
_REPO_PREFIX = re.compile(rf"(?<![A-Za-z])[A-Za-z]:(?:{_SEP}[^\\/\r\n\"'<>|*?]+?)*?{_SEP}GISclaw(?:_bundle|-main)?{_SEP}")
_USER_HOME = re.compile(rf"(?<![A-Za-z])[A-Za-z]:{_SEP}Users{_SEP}[^\\/\r\n\"'<>|*?]+(?={_SEP})")


def relativize_paths(text: str) -> str:
    """Strip machine-specific absolute prefixes so the page shows repo-relative paths."""
    text = _REPO_PREFIX.sub("", text)
    return _USER_HOME.sub("<user-home>", text)


def _display_path(run: Path) -> str:
    try:
        from kerala.config import ROOT
        return run.resolve().relative_to(ROOT.resolve()).as_posix()
    except (ImportError, ValueError):
        return run.as_posix()


def render(run: Path) -> str:
    events = []
    trace = run / "trace.jsonl"
    if trace.is_file():
        for line in trace.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                events.append({"unparsed_line": line})
    meta = _load_json(run / "meta.json") or {}
    answer = _load_json(run / "answer.json")
    title = f"{meta.get('qid', run.parent.name)} / {meta.get('arm', run.name)} — {meta.get('model_name', '')}"
    keys = ("exit_reason", "rounds", "llm_calls", "wall_seconds", "prompt_tokens", "completion_tokens",
            "native_tool_calls", "recovered_tool_calls", "git_commit")
    rows = "".join(f"<tr><td class='muted'>{html.escape(k)}</td><td>{html.escape(str(meta.get(k)))}</td></tr>" for k in keys if k in meta)
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>Trace {html.escape(title)}</title><style>{CSS}</style></head><body><main>",
             f"<h1>{html.escape(title)}</h1><p class='muted'>{html.escape(_display_path(run))}</p>",
             f"<div class='card'><table>{rows}</table></div>",
             "<div class='card'><strong>Final answer.json</strong>" + (_pre(answer) if answer is not None else "<p class='muted'>none</p>") + "</div>"]
    for event in events:
        success = event.get("success")
        status = "<span class='ok'>ok</span>" if success else ("<span class='bad'>failed</span>" if success is False else "")
        block = [f"<div class='card'><strong>Round {html.escape(str(event.get('round', '?')))}</strong> · "
                 f"<code>{html.escape(str(event.get('action', '')))}</code> {status}"]
        if event.get("thought"):
            block.append(f"<p>{html.escape(str(event['thought']))}</p>")
        if event.get("code"):
            block.append("<details open><summary>code</summary>" + _pre(event["code"]) + "</details>")
        elif event.get("args_summary") is not None:
            block.append("<details><summary>arguments</summary>" + _pre(event["args_summary"]) + "</details>")
        observation = event.get("observation_full") or event.get("observation")
        if observation:
            block.append("<details open><summary>observation</summary>" + _pre(observation) + "</details>")
        if event.get("raw_replies"):
            block.append("<details><summary>raw model replies (logging only)</summary>" + _pre(event["raw_replies"]) + "</details>")
        if "unparsed_line" in event:
            block.append(_pre(event["unparsed_line"]))
        block.append("</div>")
        parts.append("".join(block))
    parts.append("</main></body></html>")
    return relativize_paths("".join(parts))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="run folder containing trace.jsonl")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    out = args.out or args.run / "trace.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(args.run), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
