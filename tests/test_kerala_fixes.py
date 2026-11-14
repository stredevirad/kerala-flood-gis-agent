# GISclaw — an LLM agent for geospatial analysis.
# Copyright (C) 2026 Han Jinzhen
# SPDX-License-Identifier: AGPL-3.0-or-later
"""Regression tests for the upstream fixes required by KeralaFloodBench."""

import geopandas as gpd
import numpy as np
import pytest
from rasterio.crs import CRS
from rasterio.transform import Affine
from shapely.geometry import Point, Polygon

from src.agent.geo_ops import _b_count_in_polygon, _terrain


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
