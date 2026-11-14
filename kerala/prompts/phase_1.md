[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

## Phase 1: Upstream fixes F1–F5 (A5)

**Acceptance:**
```
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_fixes.py
.\.venv\Scripts\python.exe -m pytest -q tests --ignore=tests\test_ui.py
```
The second command must show no regressions against the Phase 0 baseline.
