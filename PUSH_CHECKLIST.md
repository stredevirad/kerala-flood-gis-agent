# Push checklist (for Kirito; nothing here has been run)

Nothing has been pushed. The repo has **no remote**, and the branch is `master`. Run these yourself, in PowerShell, from `D:\GISclaw_bundle`.

## 1. Before pushing: decide one thing

The five trace pages in `results/summary/matrix_gptoss_v1/traces/*.html` embed Python tracebacks and `meta.json` from the GPU PC. Those contain that PC's local Windows paths (`C:\Users\<PC user name>\…`), so the PC owner's Windows user name appears in 16 places across the 5 files. The repo will be private, but decide whether you are fine with that:
- **Keep them as they are.** No action needed.
- **Or drop them before the first push.** Remove the files and the links in `REPORT.md` §7 and `findings_r1.md` §4, then commit. They are already in local history (commit `4c5b09e`), so to keep them out of GitHub history entirely, ask for a history rewrite before pushing.

`LAPTOP_TASK.md` is untracked. Commit it or leave it out, as you prefer.

## 2. Quick re-check (local, no model calls)

```powershell
Set-Location "D:\GISclaw_bundle"
.\.venv\Scripts\python.exe -m pytest -q tests\test_kerala_frozen.py
$t = Get-ChildItem tests -Filter "test_kerala_*.py" | ForEach-Object FullName; .\.venv\Scripts\python.exe -m pytest -q $t
git status --short
```

Expected: `1 passed`; `76 passed`; and nothing listed except possibly `?? LAPTOP_TASK.md`.

## 3. Log in to GitHub (once)

```powershell
gh auth login
```

Choose GitHub.com → HTTPS → log in with a web browser.

## 4. Create the PRIVATE repo and push

```powershell
gh repo create kerala-flood-gis-agent --private --source . --remote origin --push
```

This creates `kerala-flood-gis-agent` under your account as **private**, adds it as `origin`, and pushes `master`. Then confirm:

```powershell
gh repo view kerala-flood-gis-agent --json visibility,url
git remote -v
```

`visibility` must be `PRIVATE`.

## What is already done (Step 4, 2026-11-18)

- `.gitattributes` marks the frozen files and `data/kerala/layers/*` as `-text`.
  - `kerala/bench/gold.json` is now stored in git as its exact hashed (CRLF) bytes.
  - A clone with `core.autocrlf=false` reproduces all frozen hashes, and the frozen test passes.
- Secret scan of the working tree and all 79 commits: **no real keys** (`logs/laptop/secret_scan.log`). The one hit, an OpenAI-style key, is the fake fixture `sk-abcd…` in upstream `tests/test_smoke.py`. No `.env` file was ever committed, `kerala/.env` does not exist, and `kerala/.env.example` has no values.
- `.gitignore` covers:
  - `.venv/` and `.venv_pc_stale/`;
  - `kerala/.env`;
  - `results/_profile/` (the one tracked example prompt stays tracked);
  - `results/runs/` and the per-run `dataset` links (`**/dataset`);
  - `logs/`.
- The largest tracked files are `data/kerala/layers/s1_vv_20180821_db.tif` (16.0 MB) and `dem_cop30.tif` (14.6 MB). Both are under GitHub's 100 MB limit.
