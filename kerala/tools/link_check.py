# SPDX-License-Identifier: AGPL-3.0-or-later
"""Check that relative links and images in the top-level docs point to tracked files.

Usage:
    .\\.venv\\Scripts\\python.exe -m kerala.tools.link_check [--include-untracked-index]
Uses `git ls-files` (index), so stage new files before running. Exit 1 on any broken link.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import PurePosixPath
from urllib.parse import unquote

from kerala.config import ROOT

DOCS = ("README.md", "README_KERALA.md", "REPORT.md", "INTERVIEW_PREP.md")
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)|<img[^>]+src=[\"']([^\"']+)[\"']", re.I)


def tracked() -> set[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return {p for p in out.decode("utf-8").split("\0") if p}


def main() -> int:
    files = tracked()
    dirs = {str(PurePosixPath(p).parent) for p in files}
    for p in list(dirs):
        parts = PurePosixPath(p).parts
        dirs.update(str(PurePosixPath(*parts[:i])) for i in range(1, len(parts)))
    bad = 0
    total = 0
    for doc in DOCS:
        base = PurePosixPath(doc).parent
        text = (ROOT / doc).read_text(encoding="utf-8")
        for match in LINK.finditer(text):
            target = match.group(1) or match.group(2)
            if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I) or target.startswith("#"):
                continue
            path = unquote(target.split("#", 1)[0])
            if not path:
                continue
            norm = str(PurePosixPath(*(base / path).parts)).rstrip("/")
            norm = str(PurePosixPath(norm))
            total += 1
            if norm not in files and norm not in dirs:
                bad += 1
                print(f"BROKEN {doc}: {target}")
    print(f"checked {total} relative links in {len(DOCS)} docs; broken {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
