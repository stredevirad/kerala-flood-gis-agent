# SPDX-License-Identifier: AGPL-3.0-or-later
"""Independent, deterministic KeralaFloodBench gold calculations.

This module deliberately uses GeoPandas, Shapely, Rasterio, and NumPy directly.
It does not import GISclaw agent code or use data/kerala/meta/cache outputs.
"""

from __future__ import annotations

import argparse
import inspect
import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Mapping

import geopandas as gpd
import numpy as np
import rasterio
import yaml
from rasterio.features import geometry_mask
from rasterio.transform import rowcol
from rasterio.windows import Window, from_bounds, transform as window_transform
from shapely.geometry import mapping
from shapely.ops import unary_union
from shapely.strtree import STRtree

from kerala.pack.pack import load_pack


ROOT = Path(__file__).resolve().parents[2]
LAYERS = ROOT / "data" / "kerala" / "layers"
QUESTIONS_PATH = Path(__file__).with_name("questions.yaml")
GOLD_PATH = Path(__file__).with_name("gold.json")
SENSITIVITY_PATH = Path(__file__).with_name("gold_sensitivity.json")
REVIEW_PATH = Path(__file__).with_name("GOLD_REVIEW.md")
TARGET_CRS = "EPSG:32643"
REQUIRED_QUESTION_FIELDS = {
    "id", "split", "type", "needs_params", "expected_status", "expected_unit", "text"
}
PARAMETER_LIMITS = {
    "water_threshold_vv_db": (-22.0, -13.0),
    "permanent_water_rule": (6, 12),
    "max_flood_slope_deg": (2.0, 10.0),
    "relief_camp_hospital_access_m": (1000.0, 10000.0),
    "low_lying_max_elevation_m": (3.0, 20.0),
}
FACILITY_RULES = {"representative_point", "centroid", "intersects"}


@dataclass(frozen=True)
class RasterData:
    """Aligned, agent-visible rasters and their shared grid metadata."""

    vv: np.ndarray
    seasonality: np.ndarray
    dem: np.ndarray
    transform: Any
    crs: str
    pixel_area_km2: float


@dataclass(frozen=True)
class Dataset:
    """Loaded agent-visible layers used by the independent gold functions."""

    districts: gpd.GeoDataFrame
    taluks: gpd.GeoDataFrame
    hospitals: gpd.GeoDataFrame
    schools: gpd.GeoDataFrame
    roads: gpd.GeoDataFrame
    flood: gpd.GeoDataFrame
    flood_geometry: Any
    raster: RasterData


_DERIVED_MASKS: dict[tuple[float, int, float], np.ndarray] = {}


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_questions() -> list[dict[str, Any]]:
    """Load and minimally validate the benchmark question table."""
    raw = _read_yaml(QUESTIONS_PATH)
    questions = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(questions, list):
        raise ValueError("questions.yaml must contain a questions list")
    ids = []
    for question in questions:
        if not isinstance(question, dict) or set(question) != REQUIRED_QUESTION_FIELDS:
            raise ValueError("Each question must have exactly the required Phase 4 fields")
        if question["split"] not in {"test", "dev"}:
            raise ValueError(f"{question.get('id')}: split must be test or dev")
        if question["expected_status"] not in {"ok", "cannot_answer"}:
            raise ValueError(f"{question.get('id')}: invalid expected_status")
        if not isinstance(question["needs_params"], list):
            raise ValueError(f"{question.get('id')}: needs_params must be a list")
        ids.append(question["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("Question IDs must be unique")
    return [dict(question) for question in questions]


def _read_raster(path: Path) -> tuple[np.ndarray, Any, str]:
    with rasterio.open(path) as src:
        values = src.read(1)
        transform = src.transform
        crs = src.crs.to_string() if src.crs else ""
        nodata = src.nodata
    if np.issubdtype(values.dtype, np.floating):
        values = values.astype("float64", copy=False)
        if nodata is not None and math.isfinite(float(nodata)):
            values[values == nodata] = np.nan
    return values, transform, crs


def _to_projected(frame: gpd.GeoDataFrame, label: str) -> gpd.GeoDataFrame:
    if frame.crs is None:
        raise ValueError(f"{label} has no CRS")
    return frame.to_crs(TARGET_CRS)


@lru_cache(maxsize=1)
def _dataset() -> Dataset:
    """Load only the accepted, agent-visible layer files."""
    districts = _to_projected(gpd.read_file(LAYERS / "districts.gpkg"), "districts")
    taluks = _to_projected(gpd.read_file(LAYERS / "taluks.gpkg"), "taluks")
    hospitals = _to_projected(gpd.read_file(LAYERS / "hospitals.geojson"), "hospitals")
    schools = _to_projected(gpd.read_file(LAYERS / "schools.geojson"), "schools")
    roads = _to_projected(gpd.read_file(LAYERS / "roads_major.gpkg"), "roads")
    flood = _to_projected(gpd.read_file(LAYERS / "flood_extent_20180821.gpkg"), "flood extent")
    vv, transform, crs = _read_raster(LAYERS / "s1_vv_20180821_db.tif")
    seasonality, season_transform, season_crs = _read_raster(LAYERS / "jrc_seasonality.tif")
    dem, dem_transform, dem_crs = _read_raster(LAYERS / "dem_cop30.tif")
    if crs != TARGET_CRS or season_crs != TARGET_CRS or dem_crs != TARGET_CRS:
        raise ValueError("Gold rasters must all use EPSG:32643")
    if vv.shape != seasonality.shape or vv.shape != dem.shape:
        raise ValueError("Gold rasters do not share a shape")
    if transform != season_transform or transform != dem_transform:
        raise ValueError("Gold rasters do not share a transform")
    pixel_area_km2 = abs(transform.a * transform.e - transform.b * transform.d) / 1_000_000.0
    flood_geometry = unary_union(flood.geometry.tolist())
    return Dataset(
        districts=districts,
        taluks=taluks,
        hospitals=hospitals,
        schools=schools,
        roads=roads,
        flood=flood,
        flood_geometry=flood_geometry,
        raster=RasterData(vv, seasonality, dem, transform, crs, pixel_area_km2),
    )


def clear_data_cache() -> None:
    """Clear in-process data and derived-mask caches for independent recomputation."""
    _dataset.cache_clear()
    _DERIVED_MASKS.clear()


def _district(data: Dataset, name: str):
    rows = data.districts.loc[data.districts["name"].astype(str).eq(name)]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one {name} district")
    return rows.geometry.iloc[0]


def _taluk(data: Dataset, name: str):
    rows = data.taluks.loc[data.taluks["name"].astype(str).eq(name)]
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one {name} taluk")
    return rows.geometry.iloc[0]


# GOLD:zone_mask
def _zone_mask(data: Dataset, geometry) -> np.ndarray:
    """Return a pixel-centre mask; all_touched=False is the benchmark convention."""
    return geometry_mask(
        [mapping(geometry)],
        out_shape=data.raster.vv.shape,
        transform=data.raster.transform,
        invert=True,
        all_touched=False,
    )


def _km2(pixel_count: int | np.integer, data: Dataset) -> float:
    return round(float(pixel_count) * data.raster.pixel_area_km2, 6)


def _finite_vv(data: Dataset) -> np.ndarray:
    return np.isfinite(data.raster.vv)


# GOLD:radar_flood
def _radar_flood_mask(data: Dataset, threshold_db: float, permanent_months: int, slope_deg: float) -> np.ndarray:
    """Recompute the Phase 4 VV/JRC/slope flood rule from the visible rasters."""
    key = (float(threshold_db), int(permanent_months), float(slope_deg))
    cached = _DERIVED_MASKS.get(key)
    if cached is not None:
        return cached
    dem = data.raster.dem
    safe_dem = np.where(np.isfinite(dem), dem, 0.0)
    pixel_y = abs(float(data.raster.transform.e))
    pixel_x = abs(float(data.raster.transform.a))
    gradient_y, gradient_x = np.gradient(safe_dem, pixel_y, pixel_x)
    slope = np.degrees(np.arctan(np.hypot(gradient_x, gradient_y)))
    flood = (
        _finite_vv(data)
        & np.isfinite(dem)
        & (data.raster.vv <= threshold_db)
        & (data.raster.seasonality < permanent_months)
        & (slope <= slope_deg)
    )
    _DERIVED_MASKS[key] = flood
    return flood


def _point_value(data: Dataset, point, values: np.ndarray) -> float | None:
    row, col = rowcol(data.raster.transform, point.x, point.y)
    if row < 0 or col < 0 or row >= values.shape[0] or col >= values.shape[1]:
        return None
    value = float(values[row, col])
    return value if math.isfinite(value) else None


def _facility_points(frame: gpd.GeoDataFrame, rule: str) -> gpd.GeoSeries:
    if rule == "representative_point":
        return frame.geometry.representative_point()
    if rule == "centroid":
        return frame.geometry.centroid
    raise ValueError(f"{rule} does not reduce facilities to points")


# GOLD:facility_zone
def _facility_in_zone(frame: gpd.GeoDataFrame, zone, rule: str) -> np.ndarray:
    """Apply the chosen facility rule to a district, taluk, or flood geometry."""
    if rule == "intersects":
        return frame.geometry.intersects(zone).to_numpy(dtype=bool)
    points = _facility_points(frame, rule)
    return points.apply(zone.covers).to_numpy(dtype=bool)


def _facility_subset(frame: gpd.GeoDataFrame, zone, rule: str) -> gpd.GeoDataFrame:
    return frame.loc[_facility_in_zone(frame, zone, rule)].copy()


def _geometry_intersects_mask(data: Dataset, geometry, zone_mask: np.ndarray) -> bool:
    """Test one projected facility geometry against a raster condition in its local window."""
    if geometry.geom_type == "Point":
        row, col = rowcol(data.raster.transform, geometry.x, geometry.y)
        return bool(
            0 <= row < zone_mask.shape[0]
            and 0 <= col < zone_mask.shape[1]
            and zone_mask[row, col]
        )
    window_guess = from_bounds(*geometry.bounds, transform=data.raster.transform)
    col0 = max(0, math.floor(window_guess.col_off))
    row0 = max(0, math.floor(window_guess.row_off))
    col1 = min(zone_mask.shape[1], math.ceil(window_guess.col_off + window_guess.width))
    row1 = min(zone_mask.shape[0], math.ceil(window_guess.row_off + window_guess.height))
    if col1 <= col0 or row1 <= row0:
        return False
    window = Window(col0, row0, col1 - col0, row1 - row0)
    facility_mask = geometry_mask(
        [mapping(geometry)],
        out_shape=(int(window.height), int(window.width)),
        transform=window_transform(window, data.raster.transform),
        invert=True,
        all_touched=False,
    )
    return bool(np.any(zone_mask[row0:row1, col0:col1] & facility_mask))


# GOLD:facility_lowland
def _facility_on_lowland(data: Dataset, frame: gpd.GeoDataFrame, elevation_m: float, rule: str) -> np.ndarray:
    """Apply the facility rule against cells at or below the selected elevation."""
    lowland = np.isfinite(data.raster.dem) & (data.raster.dem <= elevation_m)
    if rule == "intersects":
        return np.array(
            [_geometry_intersects_mask(data, geometry, lowland) for geometry in frame.geometry],
            dtype=bool,
        )
    return np.array(
        [
            (value is not None and value <= elevation_m)
            for value in (_point_value(data, point, data.raster.dem) for point in _facility_points(frame, rule))
        ],
        dtype=bool,
    )


# GOLD:facility_distance
def _within_hospital_distance(
    schools: gpd.GeoDataFrame,
    hospitals: gpd.GeoDataFrame,
    distance_m: float,
    rule: str,
) -> np.ndarray:
    """Return whether each school has at least one hospital within the chosen distance."""
    if schools.empty:
        return np.zeros(0, dtype=bool)
    if hospitals.empty:
        return np.zeros(len(schools), dtype=bool)
    if rule == "intersects":
        geometries = list(hospitals.geometry)
        tree = STRtree(geometries)
        result = []
        for school in schools.geometry:
            try:
                candidates = tree.query(school, predicate="dwithin", distance=distance_m)
                result.append(len(candidates) > 0)
            except (AttributeError, TypeError, ValueError):
                result.append(any(school.distance(hospital) <= distance_m for hospital in geometries))
        return np.asarray(result, dtype=bool)
    school_points = _facility_points(schools, rule)
    hospital_points = _facility_points(hospitals, rule)
    hospital_xy = np.column_stack((hospital_points.x.to_numpy(), hospital_points.y.to_numpy()))
    limit_sq = float(distance_m) ** 2
    nearby = []
    for point in school_points:
        delta = hospital_xy - np.array([point.x, point.y])
        nearby.append(bool(np.any(np.einsum("ij,ij->i", delta, delta) <= limit_sq)))
    return np.asarray(nearby, dtype=bool)


def _answer(value: Any, unit: str | None, status: str = "ok", tied: list[str] | None = None) -> dict[str, Any]:
    if isinstance(value, np.integer):
        value = int(value)
    if isinstance(value, np.floating):
        value = float(value)
    return {"value": value, "unit": unit, "status": status, "tied": list(tied or [])}


def _name_answer(scores: Mapping[str, float]) -> dict[str, Any]:
    if not scores:
        raise ValueError("A name question had no eligible candidates")
    maximum = max(scores.values())
    tied = sorted(
        name for name, score in scores.items()
        if math.isclose(score, maximum, rel_tol=0.01, abs_tol=0.0)
    )
    return _answer(tied[0], "name", tied=tied)


def _number_from_rule(value: Any, name: str, lower: float, upper: float) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be numeric")
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:\.\d+)?", value)
        if match is None:
            raise ValueError(f"{name} must contain a number")
        value = match.group(0)
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} must be numeric") from exc
    if not math.isfinite(number) or not lower <= number <= upper:
        raise ValueError(f"{name}={number} is outside the defensible range [{lower}, {upper}]")
    return number


# GOLD:parameter_normalization
def normalize_params(params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Overlay defensible direct values or pack entries on the accepted pack defaults."""
    pack = load_pack()
    values = {key: entry["value"] for key, entry in pack["parameters"].items()}
    if params:
        supplied = params.get("parameters", params) if isinstance(params, Mapping) else params
        if not isinstance(supplied, Mapping):
            raise ValueError("params must be a mapping or a loaded pack")
        for key, value in supplied.items():
            if key not in values:
                continue
            values[key] = value.get("value") if isinstance(value, Mapping) and "value" in value else value
    values["water_threshold_vv_db"] = _number_from_rule(
        values["water_threshold_vv_db"], "water_threshold_vv_db", *PARAMETER_LIMITS["water_threshold_vv_db"]
    )
    values["permanent_water_rule"] = int(round(_number_from_rule(
        values["permanent_water_rule"], "permanent_water_rule", *PARAMETER_LIMITS["permanent_water_rule"]
    )))
    values["max_flood_slope_deg"] = _number_from_rule(
        values["max_flood_slope_deg"], "max_flood_slope_deg", *PARAMETER_LIMITS["max_flood_slope_deg"]
    )
    values["relief_camp_hospital_access_m"] = _number_from_rule(
        values["relief_camp_hospital_access_m"], "relief_camp_hospital_access_m", *PARAMETER_LIMITS["relief_camp_hospital_access_m"]
    )
    values["low_lying_max_elevation_m"] = _number_from_rule(
        values["low_lying_max_elevation_m"], "low_lying_max_elevation_m", *PARAMETER_LIMITS["low_lying_max_elevation_m"]
    )
    rule = str(values["facility_point_rule"]).strip().casefold()
    if rule not in FACILITY_RULES:
        raise ValueError(f"facility_point_rule must be one of {sorted(FACILITY_RULES)}")
    values["facility_point_rule"] = rule
    return values


# GOLD:P01
def _p01(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    hospitals = _facility_subset(data.hospitals, _district(data, "Alappuzha"), params["facility_point_rule"])
    return _answer(int(_facility_in_zone(hospitals, data.flood_geometry, params["facility_point_rule"]).sum()), "count")


# GOLD:P02
def _p02(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    schools = _facility_subset(data.schools, _district(data, "Ernakulam"), params["facility_point_rule"])
    return _answer(int(_facility_in_zone(schools, data.flood_geometry, params["facility_point_rule"]).sum()), "count")


# GOLD:P03
def _p03(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    schools = _facility_subset(data.schools, _district(data, "Alappuzha"), params["facility_point_rule"])
    nearby = _within_hospital_distance(
        schools, data.hospitals, params["relief_camp_hospital_access_m"], params["facility_point_rule"]
    )
    return _answer(int((~nearby).sum()), "count")


# GOLD:P04
def _p04(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    scores: dict[str, float] = {}
    for _, taluk in data.taluks.iterrows():
        schools = _facility_subset(data.schools, taluk.geometry, params["facility_point_rule"])
        nearby = _within_hospital_distance(
            schools, data.hospitals, params["relief_camp_hospital_access_m"], params["facility_point_rule"]
        )
        scores[str(taluk["name"])] = float((~nearby).sum())
    return _name_answer(scores)


# GOLD:P05
def _p05(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    zone = _zone_mask(data, _district(data, "Alappuzha"))
    water = _finite_vv(data) & (data.raster.vv <= params["water_threshold_vv_db"])
    return _answer(_km2(int((zone & water).sum()), data), "km2")


# GOLD:P06
def _p06(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    flood = _radar_flood_mask(
        data, params["water_threshold_vv_db"], params["permanent_water_rule"], params["max_flood_slope_deg"]
    )
    zone = _zone_mask(data, _district(data, "Ernakulam"))
    return _answer(_km2(int((zone & flood).sum()), data), "km2")


# GOLD:P07
def _p07(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    flood = _radar_flood_mask(
        data, params["water_threshold_vv_db"], params["permanent_water_rule"], params["max_flood_slope_deg"]
    )
    taluk = _zone_mask(data, _taluk(data, "Kuttanad"))
    denominator = int((taluk & _finite_vv(data)).sum())
    if denominator == 0:
        raise ValueError("Kuttanad has no valid VV pixels")
    return _answer(round(100.0 * int((taluk & flood).sum()) / denominator, 6), "percent")


# GOLD:P08
def _p08(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    alappuzha = _zone_mask(data, _district(data, "Alappuzha"))
    flood = _zone_mask(data, data.flood_geometry)
    low = np.isfinite(data.raster.dem) & (data.raster.dem <= params["low_lying_max_elevation_m"])
    return _answer(_km2(int((alappuzha & flood & low).sum()), data), "km2")


# GOLD:P09
def _p09(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    low = _facility_on_lowland(
        data, data.hospitals, params["low_lying_max_elevation_m"], params["facility_point_rule"]
    )
    return _answer(int(low.sum()), "count")


# GOLD:P10
def _p10(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    flood = _zone_mask(data, data.flood_geometry)
    low = np.isfinite(data.raster.dem) & (data.raster.dem <= params["low_lying_max_elevation_m"])
    scores: dict[str, float] = {}
    for _, taluk in data.taluks.iterrows():
        taluk_mask = _zone_mask(data, taluk.geometry)
        low_count = int((taluk_mask & low).sum())
        if _km2(low_count, data) >= 10.0:
            scores[str(taluk["name"])] = float((taluk_mask & low & flood).sum()) / low_count
    return _name_answer(scores)


# GOLD:P11
def _p11(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    rule = params["facility_point_rule"]
    in_ernakulam = _facility_in_zone(data.hospitals, _district(data, "Ernakulam"), rule)
    in_flood = _facility_in_zone(data.hospitals, data.flood_geometry, rule)
    low = _facility_on_lowland(data, data.hospitals, params["low_lying_max_elevation_m"], rule)
    return _answer(int((in_ernakulam & in_flood & low).sum()), "count")


# GOLD:P12
def _p12(data: Dataset, params: Mapping[str, Any]) -> dict[str, Any]:
    rule = params["facility_point_rule"]
    schools = _facility_subset(data.schools, _district(data, "Ernakulam"), rule)
    schools = schools.loc[_facility_in_zone(schools, data.flood_geometry, rule)].copy()
    nearby = _within_hospital_distance(schools, data.hospitals, params["relief_camp_hospital_access_m"], rule)
    return _answer(int(nearby.sum()), "count")


# GOLD:C01
def _c01(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    return _answer(round(float(_district(data, "Alappuzha").area) / 1_000_000.0, 6), "km2")


# GOLD:C02
def _c02(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    ernakulam = _district(data, "Ernakulam")
    clipped = data.roads.geometry.intersection(ernakulam)
    return _answer(round(float(clipped.length.sum()) / 1000.0, 6), "km")


# GOLD:C03
def _c03(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    scores = {
        str(row["name"]): float(row.geometry.intersection(data.flood_geometry).area)
        for _, row in data.taluks.iterrows()
    }
    return _name_answer(scores)


# GOLD:C04
def _c04(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    return _answer(int(_facility_in_zone(data.hospitals, _district(data, "Ernakulam"), "representative_point").sum()), "count")


# GOLD:C05
def _c05(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    taluk = _zone_mask(data, _taluk(data, "Kuttanad"))
    values = data.raster.dem[taluk & np.isfinite(data.raster.dem)]
    if values.size == 0:
        raise ValueError("Kuttanad has no valid DEM pixels")
    return _answer(round(float(values.mean()), 6), "m")


# GOLD:C06
def _c06(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    area = _district(data, "Ernakulam").intersection(data.flood_geometry).area / 1_000_000.0
    return _answer(round(float(area), 6), "km2")


# GOLD:C07
def _c07(_data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    return _answer(None, None, status="cannot_answer")


# GOLD:C08
def _c08(_data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    return _answer(None, None, status="cannot_answer")


# GOLD:D01
def _d01(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    return _answer(int(len(data.hospitals)), "count")


# GOLD:D02
def _d02(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    return _answer(round(float(_district(data, "Ernakulam").area) / 1_000_000.0, 6), "km2")


# GOLD:D03
def _d03(data: Dataset, _params: Mapping[str, Any]) -> dict[str, Any]:
    area = _district(data, "Alappuzha").intersection(data.flood_geometry).area / 1_000_000.0
    return _answer(round(float(area), 6), "km2")


HANDLERS: dict[str, Callable[[Dataset, Mapping[str, Any]], dict[str, Any]]] = {
    "P01": _p01, "P02": _p02, "P03": _p03, "P04": _p04, "P05": _p05, "P06": _p06,
    "P07": _p07, "P08": _p08, "P09": _p09, "P10": _p10, "P11": _p11, "P12": _p12,
    "C01": _c01, "C02": _c02, "C03": _c03, "C04": _c04, "C05": _c05, "C06": _c06,
    "C07": _c07, "C08": _c08, "D01": _d01, "D02": _d02, "D03": _d03,
}


def gold_fn(qid: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Calculate one answer from accepted layers with pack defaults plus parameter overrides."""
    try:
        handler = HANDLERS[qid]
    except KeyError as exc:
        raise KeyError(f"Unknown Kerala gold question: {qid}") from exc
    result = handler(_dataset(), normalize_params(params))
    if set(result) != {"value", "unit", "status", "tied"}:
        raise AssertionError(f"{qid} returned an invalid gold result shape")
    return result


def _pack_values() -> dict[str, Any]:
    return normalize_params(load_pack())


def build_gold_answers(params: Mapping[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Compute all test and dev answers in questions.yaml order."""
    answers = {question["id"]: gold_fn(question["id"], params) for question in load_questions()}
    for question in load_questions():
        answer = answers[question["id"]]
        if answer["status"] != question["expected_status"]:
            raise AssertionError(f"{question['id']}: gold status differs from questions.yaml")
        if answer["unit"] != question["expected_unit"]:
            raise AssertionError(f"{question['id']}: gold unit differs from questions.yaml")
        if answer["status"] == "cannot_answer" and answer["value"] is not None:
            raise AssertionError(f"{question['id']}: cannot_answer gold must have null value")
    return answers


# GOLD:sensitivity
def build_sensitivity(params: Mapping[str, Any] | None = None) -> dict[str, dict[str, dict[str, Any]]]:
    """Return the stipulated non-scoring parameter sensitivity calculations."""
    baseline = normalize_params(params)
    sensitivity: dict[str, dict[str, dict[str, Any]]] = {}
    sensitivity["P05"] = {
        f"{threshold:.1f}": gold_fn("P05", {"water_threshold_vv_db": threshold})
        for threshold in (baseline["water_threshold_vv_db"] - 1.0, baseline["water_threshold_vv_db"], baseline["water_threshold_vv_db"] + 1.0)
    }
    sensitivity["P06"] = {
        f"{threshold:.1f}": gold_fn("P06", {"water_threshold_vv_db": threshold})
        for threshold in (baseline["water_threshold_vv_db"] - 1.0, baseline["water_threshold_vv_db"], baseline["water_threshold_vv_db"] + 1.0)
    }
    sensitivity["P03"] = {
        f"{distance / 1000:g} km": gold_fn("P03", {"relief_camp_hospital_access_m": distance})
        for distance in (1000.0, 3000.0, 5000.0)
    }
    sensitivity["P09"] = {
        f"{elevation:g} m": gold_fn("P09", {"low_lying_max_elevation_m": elevation})
        for elevation in (5.0, 10.0, 15.0)
    }
    return sensitivity


SOURCE_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "P01": _p01, "P02": _p02, "P03": _p03, "P04": _p04, "P05": _p05, "P06": _p06,
    "P07": _p07, "P08": _p08, "P09": _p09, "P10": _p10, "P11": _p11, "P12": _p12,
    "C01": _c01, "C02": _c02, "C03": _c03, "C04": _c04, "C05": _c05, "C06": _c06,
    "C07": _c07, "C08": _c08, "D01": _d01, "D02": _d02, "D03": _d03,
    "zone_mask": _zone_mask,
    "radar_flood": _radar_flood_mask,
    "facility_zone": _facility_in_zone,
    "facility_subset": _facility_subset,
    "facility_lowland": _facility_on_lowland,
    "facility_distance": _within_hospital_distance,
}


def _source_lines(marker: str) -> str:
    """Return the precise lines occupied by a gold handler or supporting helper."""
    try:
        source, start = inspect.getsourcelines(SOURCE_FUNCTIONS[marker])
    except KeyError as exc:
        raise ValueError(f"Missing review source mapping for {marker}") from exc
    return f"gold.py:L{start}-L{start + len(source) - 1}"


REVIEW_STEPS = {
    "P01": "Select Alappuzha hospitals using the facility rule, then count those inside the flood polygon.",
    "P02": "Select Ernakulam schools using the facility rule, then count those inside the flood polygon.",
    "P03": "Select Alappuzha schools and count those farther than the access distance from every hospital.",
    "P04": "Repeat the no-nearby-hospital count in every taluk and select the largest count, retaining 1% ties.",
    "P05": "Mask Alappuzha by pixel centre, count finite VV pixels at or below T, and multiply by 900 m².",
    "P06": "Recompute VV water, remove seasonality-permanent water and cells above the slope limit, then count Ernakulam pixels.",
    "P07": "Use the same raster flood rule in Kuttanad and divide flooded pixels by valid VV pixels in the taluk.",
    "P08": "Count Alappuzha pixel centres that are both inside the flood polygon and at or below the low-land elevation.",
    "P09": "Apply the facility rule to hospitals and count those at or below the low-land elevation.",
    "P10": "For each taluk with at least 10 km² of low land, compare its flooded-low-land share and retain 1% ties.",
    "P11": "Count hospitals that satisfy Ernakulam membership, flood membership, and low-land membership together.",
    "P12": "Select flooded Ernakulam schools and count those with a hospital within the access distance.",
    "C01": "Read the Alappuzha polygon in EPSG:32643 and convert its planar area to km².",
    "C02": "Clip each major-road line to Ernakulam and sum the clipped metre lengths as km.",
    "C03": "Intersect the flood polygon with every taluk and select the largest planar area, retaining 1% ties.",
    "C04": "Reduce hospitals to representative points and count those covered by Ernakulam.",
    "C05": "Use a pixel-centre Kuttanad mask and take the mean of finite DEM heights.",
    "C06": "Intersect the flood polygon with Ernakulam and convert its planar area to km².",
    "C07": "Return cannot_answer because the available layers contain no hospital-damage record.",
    "C08": "Return cannot_answer because the available layers contain no evacuation record.",
    "D01": "Count rows in hospitals.geojson.",
    "D02": "Read the Ernakulam polygon in EPSG:32643 and convert its planar area to km².",
    "D03": "Intersect the flood polygon with Alappuzha and convert its planar area to km².",
}


REVIEW_HELPERS = {
    "P01": ["facility_subset", "facility_zone"], "P02": ["facility_subset", "facility_zone"],
    "P03": ["facility_subset", "facility_distance"],
    "P04": ["facility_subset", "facility_distance"], "P05": ["zone_mask"], "P06": ["radar_flood", "zone_mask"],
    "P07": ["radar_flood", "zone_mask"], "P08": ["zone_mask"], "P09": ["facility_lowland"],
    "P10": ["zone_mask"], "P11": ["facility_zone", "facility_lowland"],
    "P12": ["facility_subset", "facility_zone", "facility_distance"],
    "C04": ["facility_zone"], "C05": ["zone_mask"],
}


def _format_value(answer: Mapping[str, Any]) -> str:
    if answer["status"] == "cannot_answer":
        return "cannot_answer (value and unit are null)"
    value = answer["value"]
    if isinstance(value, float):
        return f"{value:.6f} {answer['unit']}"
    return f"{value} {answer['unit']}"


def _sanity_records(answers: Mapping[str, Mapping[str, Any]], data: Dataset, params: Mapping[str, Any]) -> dict[str, tuple[bool, str]]:
    rule = params["facility_point_rule"]
    hospitals_alappuzha = int(_facility_in_zone(data.hospitals, _district(data, "Alappuzha"), rule).sum())
    schools_alappuzha = int(_facility_in_zone(data.schools, _district(data, "Alappuzha"), rule).sum())
    hospitals_ernakulam = int(_facility_in_zone(data.hospitals, _district(data, "Ernakulam"), rule).sum())
    schools_ernakulam_flooded = answers["P02"]["value"]
    alappuzha_area = float(_district(data, "Alappuzha").area / 1_000_000.0)
    ernakulam_area = float(_district(data, "Ernakulam").area / 1_000_000.0)
    dem_values = data.raster.dem[np.isfinite(data.raster.dem)]
    taluk_names = set(data.taluks["name"].astype(str))
    return {
        "P01": (0 <= answers["P01"]["value"] <= hospitals_alappuzha, f"P01 is no greater than the {hospitals_alappuzha} hospitals assigned to Alappuzha."),
        "P02": (0 <= answers["P02"]["value"] <= len(data.schools), "P02 is no greater than the mapped school count."),
        "P03": (0 <= answers["P03"]["value"] <= schools_alappuzha, f"P03 is no greater than the {schools_alappuzha} schools assigned to Alappuzha."),
        "P04": (answers["P04"]["value"] in taluk_names, "P04 names a taluk present in taluks.gpkg."),
        "P05": (0 <= answers["P05"]["value"] <= alappuzha_area, "P05 is between zero and Alappuzha's planar area."),
        "P06": (0 <= answers["P06"]["value"] <= ernakulam_area, "P06 is between zero and Ernakulam's planar area."),
        "P07": (0 <= answers["P07"]["value"] <= 100, "P07 is a percentage between zero and 100."),
        "P08": (0 <= answers["P08"]["value"] <= alappuzha_area, "P08 is between zero and Alappuzha's planar area."),
        "P09": (0 <= answers["P09"]["value"] <= len(data.hospitals), "P09 is no greater than the mapped hospital count."),
        "P10": (answers["P10"]["value"] in taluk_names, "P10 names a taluk present in taluks.gpkg."),
        "P11": (0 <= answers["P11"]["value"] <= hospitals_ernakulam, f"P11 is no greater than the {hospitals_ernakulam} hospitals assigned to Ernakulam."),
        "P12": (0 <= answers["P12"]["value"] <= schools_ernakulam_flooded, "P12 is no greater than P02's flooded Ernakulam-school count."),
        "C01": (answers["C01"]["value"] > 0, "C01 is a positive projected polygon area."),
        "C02": (answers["C02"]["value"] > 0, "C02 is a positive clipped-road length."),
        "C03": (answers["C03"]["value"] in taluk_names, "C03 names a taluk present in taluks.gpkg."),
        "C04": (0 <= answers["C04"]["value"] <= len(data.hospitals), "C04 is no greater than the mapped hospital count."),
        "C05": (float(dem_values.min()) <= answers["C05"]["value"] <= float(dem_values.max()), "C05 lies within the finite DEM range."),
        "C06": (0 <= answers["C06"]["value"] <= ernakulam_area, "C06 is between zero and Ernakulam's planar area."),
        "C07": (answers["C07"] == _answer(None, None, status="cannot_answer"), "C07 is unavailable from the supplied layers."),
        "C08": (answers["C08"] == _answer(None, None, status="cannot_answer"), "C08 is unavailable from the supplied layers."),
        "D01": (answers["D01"]["value"] == len(data.hospitals), "D01 equals the hospitals.geojson row count."),
        "D02": (answers["D02"]["value"] > 0, "D02 is a positive projected polygon area."),
        "D03": (0 <= answers["D03"]["value"] <= alappuzha_area, "D03 is between zero and Alappuzha's planar area."),
    }


def _review_document(
    answers: Mapping[str, Mapping[str, Any]],
    sanity: Mapping[str, tuple[bool, str]],
    params: Mapping[str, Any],
) -> str:
    lines = [
        "# KeralaFloodBench gold review",
        "",
        "This review is generated from `gold.py` and the accepted Phase 2 layers. It is not frozen until Kirito replies `gold approved`.",
        "",
        "## Calculation basis",
        "",
        f"- Default water threshold: {params['water_threshold_vv_db']:.1f} dB, resolved from the accepted manifest through the pack.",
        f"- Flood-rule defaults: seasonality < {params['permanent_water_rule']}, slope <= {params['max_flood_slope_deg']:g} degrees.",
        f"- Other defaults: low land <= {params['low_lying_max_elevation_m']:g} m; hospital access <= {params['relief_camp_hospital_access_m'] / 1000:g} km; facility rule = `{params['facility_point_rule']}`.",
        "- Raster masks use pixel centres (`all_touched=False`) on the 30 m grid. P06 and P07 recompute the VV/JRC/DEM rule from the agent-visible rasters rather than reuse a Phase 2 cache output.",
        "",
        "## Full gold table",
        "",
        "| ID | Gold value | Status | Tied names |",
        "|---|---:|---|---|",
    ]
    for question in load_questions():
        answer = answers[question["id"]]
        tied = ", ".join(answer["tied"]) or "—"
        lines.append(f"| {question['id']} | {_format_value(answer)} | {answer['status']} | {tied} |")
    for question in load_questions():
        qid = question["id"]
        answer = answers[qid]
        refs = [_source_lines(qid)] + [_source_lines(marker) for marker in REVIEW_HELPERS.get(qid, [])]
        passed, statement = sanity[qid]
        lines.extend([
            "",
            f"## {qid}",
            "",
            f"- Gold value: `{_format_value(answer)}`; status `{answer['status']}`; tied names: `{', '.join(answer['tied']) or 'none'}`.",
            f"- Steps: {REVIEW_STEPS[qid]}",
            f"- Computing code: {', '.join(refs)}.",
            f"- Sanity: {'PASS' if passed else 'FAIL'} — {statement}",
        ])
    return "\n".join(lines) + "\n"


def _payload(answers: Mapping[str, Mapping[str, Any]], params: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": 1, "parameters": dict(params), "answers": dict(answers)}


def _sensitivity_payload(sensitivity: Mapping[str, Any], params: Mapping[str, Any]) -> dict[str, Any]:
    return {"schema_version": 1, "parameters": dict(params), "answers": dict(sensitivity)}


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_gold_outputs() -> tuple[dict[str, Any], dict[str, Any], str]:
    """Build and write gold.json, gold_sensitivity.json, and GOLD_REVIEW.md."""
    clear_data_cache()
    params = _pack_values()
    answers = build_gold_answers(params)
    sensitivity = build_sensitivity(params)
    sanity = _sanity_records(answers, _dataset(), params)
    if not all(passed for passed, _ in sanity.values()):
        failed = [qid for qid, (passed, _) in sanity.items() if not passed]
        raise AssertionError(f"Gold sanity checks failed: {failed}")
    gold_payload = _payload(answers, params)
    sensitivity_payload = _sensitivity_payload(sensitivity, params)
    review = _review_document(answers, sanity, params)
    _write_json(GOLD_PATH, gold_payload)
    _write_json(SENSITIVITY_PATH, sensitivity_payload)
    REVIEW_PATH.write_text(review, encoding="utf-8")
    return gold_payload, sensitivity_payload, review


def check_gold_outputs() -> None:
    """Recompute the gold table twice and check deterministic stored artifacts."""
    clear_data_cache()
    params_first = _pack_values()
    answers_first = build_gold_answers(params_first)
    sensitivity_first = build_sensitivity(params_first)
    sanity = _sanity_records(answers_first, _dataset(), params_first)
    if not all(passed for passed, _ in sanity.values()):
        failed = [qid for qid, (passed, _) in sanity.items() if not passed]
        raise AssertionError(f"Gold sanity checks failed: {failed}")
    clear_data_cache()
    params_second = _pack_values()
    answers_second = build_gold_answers(params_second)
    sensitivity_second = build_sensitivity(params_second)
    if params_first != params_second or answers_first != answers_second or sensitivity_first != sensitivity_second:
        raise AssertionError("Two independent gold recomputations differ")
    expected_gold = _payload(answers_first, params_first)
    expected_sensitivity = _sensitivity_payload(sensitivity_first, params_first)
    if not GOLD_PATH.is_file() or json.loads(GOLD_PATH.read_text(encoding="utf-8")) != expected_gold:
        raise AssertionError("gold.json does not match the independent recomputation")
    if not SENSITIVITY_PATH.is_file() or json.loads(SENSITIVITY_PATH.read_text(encoding="utf-8")) != expected_sensitivity:
        raise AssertionError("gold_sensitivity.json does not match the independent recomputation")
    expected_review = _review_document(answers_first, sanity, params_first)
    if not REVIEW_PATH.is_file() or REVIEW_PATH.read_text(encoding="utf-8") != expected_review:
        raise AssertionError("GOLD_REVIEW.md does not match the independent recomputation")
    print(f"Gold check passed: {len(answers_first)} answers, {len(sensitivity_first)} sensitivity groups")
    for qid in ("P01", "P07", "C01"):
        print(f"{qid}: {_format_value(answers_first[qid])}")
    print("Both independent recomputations matched; all sanity statements passed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="recompute twice and verify stored gold artifacts")
    args = parser.parse_args(argv)
    if args.check:
        check_gold_outputs()
    else:
        gold_payload, sensitivity_payload, _review = write_gold_outputs()
        print(f"Wrote {len(gold_payload['answers'])} gold answers to {GOLD_PATH}")
        print(f"Wrote {len(sensitivity_payload['answers'])} sensitivity groups to {SENSITIVITY_PATH}")
        print(f"Wrote review to {REVIEW_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
