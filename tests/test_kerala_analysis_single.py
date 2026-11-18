# SPDX-License-Identifier: AGPL-3.0-or-later
"""analysis.py runs the P01 part on a single repeat without needing a second one."""

from __future__ import annotations

import csv

from kerala.bench import analysis

FIELDS = ["batch", "model", "qid", "arm", "correct_final", "params_reported", "exit_reason"]


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_single_repeat_skips_agreement_and_other_batches(tmp_path):
    rows = [
        {"batch": "r1", "model": "m", "qid": "C01", "arm": "noparam", "correct_final": "True", "params_reported": "{}", "exit_reason": "finished"},
        {"batch": "r2", "model": "m", "qid": "C01", "arm": "noparam", "correct_final": "False", "params_reported": "{}", "exit_reason": "finished"},
    ]
    _write(tmp_path / "per_run.csv", rows)
    (tmp_path / "results_tables.md").write_text("# tables\n", encoding="utf-8")

    assert analysis.main(["--summary", str(tmp_path), "--first", "r1"]) == 0

    text = (tmp_path / "analysis.md").read_text(encoding="utf-8")
    assert analysis.SECTION_SINGLE in text
    assert "Run-to-run agreement is not computed" in text
    assert "Cohen" not in text
    assert not (tmp_path / "agreement.csv").exists()
    assert not (tmp_path / "agreement_cells.csv").exists()
    tables = (tmp_path / "results_tables.md").read_text(encoding="utf-8")
    assert tables.startswith("# tables") and tables.count(analysis.SECTION_SINGLE) == 1

    # Re-running replaces the section instead of appending a second copy.
    assert analysis.main(["--summary", str(tmp_path), "--first", "r1"]) == 0
    tables = (tmp_path / "results_tables.md").read_text(encoding="utf-8")
    assert tables.count(analysis.SECTION_SINGLE) == 1
