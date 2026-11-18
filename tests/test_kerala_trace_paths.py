# SPDX-License-Identifier: AGPL-3.0-or-later
"""trace_html strips machine-specific absolute paths from rendered pages."""

from __future__ import annotations

import json

from kerala.bench import trace_html


def test_relativize_single_and_double_backslash_forms():
    text = (
        'File "C:\\Users\\Some User\\Downloads\\GISclaw_bundle\\src\\agent\\sandbox.py", line 2 | '
        "json: <module 'json' from 'C:\\\\Users\\\\Some User\\\\AppData\\\\Roaming\\\\uv\\\\python\\\\json.py'> | "
        "D:\\GISclaw_bundle\\results\\runs\\x"
    )
    out = trace_html.relativize_paths(text)
    assert "Some User" not in out
    assert 'File "src\\agent\\sandbox.py"' in out
    assert "<user-home>\\\\AppData" in out
    assert "| results\\runs\\x" in out


def test_render_contains_no_absolute_user_path(tmp_path):
    run = tmp_path / "P01" / "pack"
    run.mkdir(parents=True)
    event = {"round": 1, "action": "execute", "success": False,
             "observation": 'Traceback\n  File "C:\\Users\\Some User\\GISclaw_bundle\\src\\agent\\sandbox.py", line 9'}
    (run / "trace.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
    (run / "meta.json").write_text(json.dumps({"qid": "P01", "arm": "pack"}), encoding="utf-8")
    page = trace_html.render(run)
    assert "Some User" not in page and "Users\\" not in page
    assert "src\\agent\\sandbox.py" in page
