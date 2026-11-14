# GISclaw — an LLM agent for geospatial analysis.
# Copyright (C) 2026 Han Jinzhen
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression tests for the upstream fixes required by KeralaFloodBench."""

import builtins
import json
from unittest.mock import patch

import geopandas as gpd
import numpy as np
import pytest
from rasterio.crs import CRS
from rasterio.transform import Affine
from shapely.geometry import Point, Polygon

from src.agent.geo_ops import _b_count_in_polygon, _terrain
from src.agent.react_agent import GISReActAgent


def test_count_in_polygon_does_not_count_empty_left_join_rows(tmp_path, monkeypatch):
    polys = gpd.GeoDataFrame(
        {"name": ["A", "B"]},
        geometry=[
            Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),
            Polygon([(3, 0), (5, 0), (5, 2), (3, 2)]),
        ],
        crs="EPSG:32643",
    )
    points = gpd.GeoDataFrame(
        geometry=[Point(0.5, 0.5), Point(1.5, 1.5)],
        crs="EPSG:32643",
    )
    monkeypatch.chdir(tmp_path)
    namespace = {"polys": polys, "points": points}

    code = _b_count_in_polygon(
        {"polygons": "polys", "points": "points"}, {}, "counted", None
    )
    exec(code, namespace)

    assert namespace["counted"]["NUMPOINTS"].tolist() == [2, 0]


def _terrain_code(kind, crs):
    return _terrain(kind)(
        {"raster": "dem"},
        {},
        "terrain",
        None,
    ), {
        "dem": np.array([[0.0, 0.01], [0.0, 0.01]]),
        "dem_meta": {
            "crs": crs,
            "transform": Affine(1, 0, 500000, 0, -1, 5000000),
            "nodata": None,
        },
    }


@pytest.mark.parametrize("kind", ["slope", "aspect", "hillshade"])
def test_terrain_skips_geographic_crs(kind, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    code, namespace = _terrain_code(kind, CRS.from_epsg(4326))

    exec(code, namespace)

    output = capsys.readouterr().out
    assert output.startswith("❌")
    assert "reprojected to a projected CRS" in output
    assert "terrain" not in namespace


def test_slope_of_projected_one_percent_ramp_is_about_057_degrees(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    code, namespace = _terrain_code(kind="slope", crs=CRS.from_epsg(32643))

    exec(code, namespace)

    assert np.allclose(namespace["terrain"], 0.5729, atol=0.001)


def test_code_py_is_written_as_utf8_with_degree_and_malayalam(tmp_path, monkeypatch):
    import src.agent.react_agent as react_agent

    monkeypatch.setattr(react_agent, "_link_dataset", lambda *_args: None)
    code = (
        "open('pred_results/notes.txt', 'w', encoding='utf-8')"
        ".write('° മലയാളം')"
    )
    replies = iter([
        "Thought: save text\nAction: execute\nArgs: "
        + json.dumps({"code": code}, ensure_ascii=False),
        'Thought: done\nAction: finish\nArgs: {"summary": "Saved."}',
    ])

    class Engine:
        def generate(self, **_kwargs):
            return {"text": next(replies)}

    result = GISReActAgent(Engine(), verbose=False).run(
        "Write a UTF-8 note.",
        data_dir=str(tmp_path),
        work_dir=str(tmp_path / "work"),
    )

    assert result.success
    code_bytes = (tmp_path / "work" / "code.py").read_bytes()
    assert "° മലയാളം" in code_bytes.decode("utf-8")


def test_csv_output_guard_uses_utf8_with_replacement(tmp_path):
    pred_dir = tmp_path / "pred_results"
    pred_dir.mkdir()
    csv_path = pred_dir / "rows.csv"
    csv_path.write_bytes(b"name\nvalue-\xff\n")
    agent = GISReActAgent(None, verbose=False)

    with patch("builtins.open", wraps=builtins.open) as open_mock:
        issues = agent._validate_outputs(str(tmp_path))

    assert issues == ""
    open_mock.assert_called_once_with(
        str(csv_path), encoding="utf-8", errors="replace"
    )


def test_conversation_trimming_obeys_context_budget_without_cutting_header():
    agent = GISReActAgent(None, context_chars=4000, verbose=False)
    header = "Task: preserve this complete task header."
    history = [
        ("assistant" if index % 2 == 0 else "user",
         f"entry-{index} " + ("x" * 1400) + f" tail-{index}")
        for index in range(20)
    ]
    history[-1] = ("user", "last exchange " + ("y" * 1400) + " LAST-ENTRY-TAIL")

    formatted = agent._format_conversation(header, history)

    assert formatted.startswith(header)
    assert "LAST-ENTRY-TAIL" in formatted
    assert "…(trimmed)…" in formatted
    assert len(formatted) <= 4000 + len(header) + 300
