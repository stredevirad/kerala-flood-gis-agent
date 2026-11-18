# SPDX-License-Identifier: AGPL-3.0-or-later
"""Completeness check for results/summary/number_check.md (no model calls).

Extracts every number written in REPORT.md, README_KERALA.md and
INTERVIEW_PREP.md, and reports any number that does not appear in the
"Number(s)" column of `results/summary/number_check.md`. Skipped:
inline code and link targets; question/arm/fix ids (P01, A2, F8); list
and heading numerals. Exit code 1 if anything is unlisted.

Usage:
    .\\.venv\\Scripts\\python.exe -m kerala.tools.number_check
"""

from __future__ import annotations

import re
import sys

from kerala.config import ROOT

DOCS = ("README.md", "REPORT.md", "README_KERALA.md", "INTERVIEW_PREP.md")
CHECK = ROOT / "results" / "summary" / "number_check.md"
NUMBER = re.compile(r"(?<![\w/.])[−-]?\d[\d,]*(?:\.\d+)?")


def _normalise(token: str) -> str:
    return token.replace("−", "-").rstrip(",.").replace(",", "")


def doc_numbers(text: str) -> set[str]:
    found: set[str] = set()
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        line = re.sub(r"`[^`]*`", " ", line)
        line = re.sub(r"\]\([^)]*\)", "]", line)
        line = re.sub(r"\b[PCDFA]\d{1,2}\b", " ", line)
        line = re.sub(r"^\s*(?:#+\s*)?\d+\.\s", " ", line)
        line = re.sub(r"\b(?:gpt-oss:20b|qwen2\.5-coder:7b|qwen3\.5:9b|gemini-3\.5-flash-lite)\b", " ", line, flags=re.I)
        line = re.sub(r"\b(?:Qwen ?2\.5-Coder 7B|Qwen ?3\.5(?: 9B)?|Gemini 3\.5|gpt-oss 20B|20B|9B|7B)\b", " ", line, flags=re.I)
        found.update(_normalise(m) for m in NUMBER.findall(line))
    return {n for n in found if n and n != "-"}


def listed_numbers(text: str) -> set[str]:
    listed: set[str] = set()
    for line in text.splitlines():
        if not line.startswith("|") or line.startswith("|---"):
            continue
        cells = line.split("|")
        if len(cells) > 2:
            listed.update(_normalise(m) for m in NUMBER.findall(cells[1].replace("`", "")))
    return listed


def main() -> int:
    listed = listed_numbers(CHECK.read_text(encoding="utf-8"))
    missing = {}
    for doc in DOCS:
        numbers = doc_numbers((ROOT / doc).read_text(encoding="utf-8"))
        gap = sorted(numbers - listed, key=lambda s: (len(s), s))
        if gap:
            missing[doc] = gap
        print(f"{doc}: {len(numbers)} distinct numbers, {len(numbers) - len(gap)} listed")
    for doc, gap in missing.items():
        print(f"UNLISTED in {doc}: {', '.join(gap)}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
