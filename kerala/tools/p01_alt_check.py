# SPDX-License-Identifier: AGPL-3.0-or-later
"""P01 alternative-method grid (local analysis only; no model calls).

Recomputes the P01 count ("flood-affected hospitals in Alappuzha") with the
independent gold helpers, but varies three method choices that agent runs
were seen to make in their traces: the facility rule (representative_point,
centroid, intersects), the flood buffer (0, 100, 250, 500 m) and the district
filter (Alappuzha only, as the question asks, or both study districts, i.e. the
filter was skipped). Gold values and frozen files are only read, never changed.

Usage:
    .\\.venv\\Scripts\\python.exe -m kerala.tools.p01_alt_check --out results\\summary\\matrix_gptoss_v1\\p01_alt_grid.md
"""

from __future__ import annotations

import argparse
from pathlib import Path

from shapely.ops import unary_union

from kerala.bench import gold
from kerala.config import ROOT

RULES = ("representative_point", "centroid", "intersects")
BUFFERS = (0.0, 100.0, 250.0, 500.0)


def grid() -> list[dict[str, object]]:
    data = gold._dataset()
    zones = {
        "Alappuzha (as asked)": gold._district(data, "Alappuzha"),
        "both districts (filter skipped)": unary_union(data.districts.geometry.tolist()),
    }
    rows = []
    for zone_name, zone in zones.items():
        for rule in RULES:
            subset = gold._facility_subset(data.hospitals, zone, rule)
            for buffer_m in BUFFERS:
                count = int(gold._facility_within_flood_buffer(subset, data.flood_geometry, buffer_m, rule).sum())
                rows.append({"zone": zone_name, "rule": rule, "buffer_m": buffer_m, "count": count})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    out = args.out if args.out.is_absolute() else ROOT / args.out
    rows = grid()
    official = gold.gold_fn("P01")["value"]
    lines = [
        "# P01 alternative-method grid",
        "",
        f"Official gold (representative_point, 250 m, Alappuzha): **{official}**.",
        "Produced by `kerala.tools.p01_alt_check` from the independent gold helpers (no model calls).",
        "",
        "| District filter | Facility rule | Buffer m | P01 count |",
        "|---|---|---:|---:|",
    ]
    lines += [f"| {r['zone']} | {r['rule']} | {r['buffer_m']:g} | {r['count']} |" for r in rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
