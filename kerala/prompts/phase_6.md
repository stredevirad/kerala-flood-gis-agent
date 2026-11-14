[Part A: Shared context](../MASTERPROMPT.md#part-a-shared-context-applies-to-every-session)

## Phase 6: After I say "matrix done": score, analyse, write

1. Run `score.py`.
2. Read at least 10 failed traces spread across the taxonomy labels.
3. **Draft `REPORT.md`** with real numbers only, and leave `TODO(Kirito)` markers for the manual taxonomy and interpretation. Sections:
   1. **Problem.**
   2. **Related work.**
      - GISclaw (arXiv 2603.26845): single-agent was best on large models; 14B improved from 52% to 79% with planner+worker; domain parameters were a failure point.
      - GeoAnalystBench.
      - The UN-SPIDER practice.
      - Vishnu et al. 2019.
   3. **System.**
      - A Mermaid diagram.
      - What was reused vs added.
      - F1–F5 with before/after.
      - The documented upstream issues.
   4. **Data and pack.**
      - Sources, CRS, the reference-flood method and T.
      - Each parameter with its kind and provenance.
   5. **Benchmark design.**
      - The arms, and why parameter names are given to every arm.
      - Controls, the independence of gold, tolerances, the freeze.
      - The pre-registered expectation.
   6. **Results.**
      - The per-question table and the paired tables.
      - First attempt vs final.
      - `correct_given_own_params`.
      - The cloud ceiling.
      - Cost (minutes and tokens per correct answer) on a 16 GB laptop.
   7. **Failure taxonomy.** Three annotated traces.
   8. **Limitations.**
      - 20 questions, one seed;
      - SAR misses water under vegetation and in urban areas (Ernakulam);
      - partial recession by 21 Aug;
      - OSM data is from today, not 2018;
      - conventions are choices, with a sensitivity figure.
   9. **Future work.**
   10. **Attributions:**
       - © OpenStreetMap contributors (ODbL);
       - Copernicus Sentinel data 2018 (RTC via Microsoft Planetary Computer);
       - Copernicus DEM GLO-30 © DLR e.V. 2010–2014 and © Airbus Defence and Space GmbH 2014–2018, provided under COPERNICUS by the European Union and ESA;
       - JRC Global Surface Water (Pekel et al. 2016);
       - GISclaw © Han Jinzhen (AGPL-3.0).
4. **Write `README_KERALA.md`.** Cover what the project is, exact reproduction commands, the attributions, and the licence.
5. **Write `INTERVIEW_PREP.md`.** It holds plain-language explanations I must be able to give:
   - SAR backscatter and dB;
   - the Otsu threshold;
   - why UTM is used for areas;
   - representative point vs centroid;
   - the three arms and why parameter names go to every arm;
   - `correct_given_own_params`;
   - the sign test, and why it is only descriptive;
   - F1–F5;
   - the top 3 failure modes, each with its trace path;
   - 10 likely interviewer questions with short answers drawn from our actual results.
6. **Extras** (in this order, only after 1–5 are done):
   1. `kerala\upstream\F1.patch`, `F2.patch` and `PR_F1_F2.md`, a ready-to-paste PR body with before/after numbers. Do not push.
   2. `kerala\bench\trace_html.py`: a standard-library-only HTML viewer for a `trace.jsonl` file. Link the three annotated traces from `REPORT.md`.

**Acceptance:** every number in `REPORT.md` appears in `results\summary\results_tables.md` or in the manifest. Run a small script that checks this and paste its output.

### Appendix: `PROGRESS.md` template
```
# PROGRESS
## Status: Phase <n> — <in progress | done | blocked | STOP: waiting for Kirito>
## Checklist
- [ ] Phase 0
  - [ ] 0.1 git init + .gitignore …  (one line per sub-step)
- [ ] Phase 1 …
## Numbers so far
(timing table, baseline tests, T, flood km² per district, taluks, gold table, smoke results)
## Decisions made (with reason)
## Needs Kirito
## Last acceptance output
(command + last 15 lines)
```

---

## Start now

Do Phase 0. Stop at its STOP gate.
