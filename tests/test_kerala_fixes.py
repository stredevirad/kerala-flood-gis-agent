# GISclaw — an LLM agent for geospatial analysis.
# Copyright (C) 2026 Han Jinzhen
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression tests for the upstream fixes required by KeralaFloodBench."""

import geopandas as gpd
from shapely.geometry import Point, Polygon

from src.agent.geo_ops import _b_count_in_polygon


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
