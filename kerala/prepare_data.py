# SPDX-License-Identifier: AGPL-3.0-or-later
"""Prepare the reproducible KeralaFloodBench input layers."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import pandas as pd
import planetary_computer as pc
import rasterio
from pystac_client import Client
from rasterio.features import geometry_mask, shapes
from rasterio.transform import from_origin, rowcol
from rasterio.warp import Resampling, reproject, transform_bounds
from rasterio.windows import Window, bounds as window_bounds, transform as window_transform
from shapely.geometry import Point, mapping, shape
from shapely.ops import unary_union


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data" / "kerala"
LAYERS = DATA_ROOT / "layers"
META = DATA_ROOT / "meta"
CACHE = META / "cache"
STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
NASA_EXPORT_URL = (
    "https://maps.disasters.nasa.gov/ags03/rest/services/Kerala_India_Flood/"
    "Sentinel1_20180821_water_extent/MapServer/export"
)
TARGET_CRS = "EPSG:32643"
SOURCE_NODATA_S1 = -32768
NODATA_JRC = 255
PIXEL_SIZE = 30
MAX_PIXELS = 25_000_000
TILE = 512
VV_HIST_MIN_DB = -30.0
VV_HIST_MAX_DB = 5.0
VV_HIST_BIN_WIDTH_DB = 0.1
VV_HIST_BIN_COUNT = int(round((VV_HIST_MAX_DB - VV_HIST_MIN_DB) / VV_HIST_BIN_WIDTH_DB))
DISTRICTS = ("Ernakulam", "Alappuzha")
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api",
    "https://overpass.private.coffee/api",
)
EXPECTED_S1_PREFIXES = (
    "S1A_IW_GRDH_1SDV_20180821T004044_",
    "S1A_IW_GRDH_1SDV_20180821T004109_",
)
EXPECTED_LAYERS = {
    "districts.gpkg": TARGET_CRS,
    "taluks.gpkg": TARGET_CRS,
    "hospitals.geojson": "EPSG:4326",
    "schools.geojson": "EPSG:4326",
    "roads_major.gpkg": TARGET_CRS,
    "s1_vv_20180821_db.tif": TARGET_CRS,
    "jrc_seasonality.tif": TARGET_CRS,
    "dem_cop30.tif": TARGET_CRS,
    "flood_extent_20180821.gpkg": TARGET_CRS,
}
GDAL_OPTIONS = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_HTTP_CONNECTTIMEOUT": "30",
    "GDAL_HTTP_TIMEOUT": "90",
    "GDAL_HTTP_MAX_RETRY": "2",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "VSI_CACHE": "FALSE",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.stem + ".partial" + path.suffix)
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temp, path)


def _atomic_vector_write(gdf: gpd.GeoDataFrame, path: Path, driver: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.stem + ".partial" + path.suffix)
    if temp.exists():
        temp.unlink()
    if driver == "GPKG":
        gdf.to_file(temp, driver=driver, index=False)
    else:
        gdf.to_file(temp, driver=driver, index=False)
    os.replace(temp, path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _text(value: Any) -> str | None:
    if isinstance(value, (list, tuple)):
        value = next((part for part in value if isinstance(part, str) and part.strip()), None)
    if value is None or value is pd.NA:
        return None
    if np.isscalar(value):
        try:
            if bool(pd.isna(value)):
                return None
        except (TypeError, ValueError):
            pass
    result = str(value).strip()
    return result or None


def _osm_id(row: Any) -> int | str | None:
    value = row.get("id", row.get("osmid"))
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)


def _keep_expected_geometries(frame: gpd.GeoDataFrame, kind: str) -> gpd.GeoDataFrame:
    expected = {"Point", "Polygon", "MultiPolygon"} if kind == "facility" else {"LineString"}
    keep = [
        geom is not None and not geom.is_empty and geom.geom_type in expected
        for geom in frame.geometry
    ]
    return frame.loc[keep].copy()


def _geometry_counts(frame: gpd.GeoDataFrame) -> dict[str, int]:
    counts = frame.geometry.geom_type.value_counts(dropna=False).to_dict()
    return {str(name) if name is not None else "Null": int(count) for name, count in counts.items()}


def _element_geometry_counts(frame: gpd.GeoDataFrame) -> dict[str, dict[str, int]]:
    elements = frame["element"].fillna("unknown").astype(str) if "element" in frame else pd.Series(
        ["unknown"] * len(frame), index=frame.index
    )
    geometries = frame.geometry.geom_type.fillna("Null").astype(str)
    pairs = pd.DataFrame({"element": elements.to_numpy(), "geometry": geometries.to_numpy()})
    counts = pairs.value_counts().to_dict()
    result: dict[str, dict[str, int]] = {}
    for (element, geometry), count in counts.items():
        result.setdefault(element, {})[geometry] = int(count)
    return result


def _validate_vector_layer(frame: gpd.GeoDataFrame, filename: str) -> dict[str, int]:
    if frame.geometry.isna().any():
        raise ValueError(f"{filename} has {int(frame.geometry.isna().sum())} null geometries")
    if frame.geometry.is_empty.any():
        raise ValueError(f"{filename} has {int(frame.geometry.is_empty.sum())} empty geometries")
    types = set(frame.geometry.geom_type.dropna().unique())
    if filename in {"hospitals.geojson", "schools.geojson"}:
        unexpected = types - {"Point", "Polygon", "MultiPolygon"}
        if unexpected:
            raise ValueError(f"{filename} has unexpected geometry types: {sorted(unexpected)}")
        if "geom_kind" not in frame:
            raise ValueError(f"{filename} is missing geom_kind")
        mismatched = frame.geom_kind.astype(str) != frame.geometry.geom_type.astype(str)
        if mismatched.any():
            raise ValueError(f"{filename} has {int(mismatched.sum())} geom_kind/geometry mismatches")
    elif filename == "roads_major.gpkg" and types - {"LineString"}:
        raise ValueError(f"{filename} has non-LineString geometries: {sorted(types)}")
    return _geometry_counts(frame)


def _load_aoi() -> gpd.GeoDataFrame:
    path = CACHE / "aoi.geojson"
    if path.exists():
        return gpd.read_file(path).to_crs("EPSG:4326")

    print("Phase 2.1: geocoding Ernakulam and Alappuzha", flush=True)
    rows: list[dict[str, Any]] = []
    geocode_error: Exception | None = None
    try:
        found = ox.geocode_to_gdf(
            [f"{district} district, Kerala, India" for district in DISTRICTS]
        )
        for district in DISTRICTS:
            candidates = found[
                found["name"].astype(str).str.casefold().eq(district.casefold())
            ]
            if candidates.empty:
                raise ValueError(f"Nominatim did not return an exact {district} match")
            geom = candidates.geometry.iloc[0]
            rows.append({"name": district, "geometry": geom})
    except Exception as exc:
        geocode_error = exc
        print(f"Nominatim geocoding failed; using OSM admin_level=5 fallback: {exc}", flush=True)
        try:
            candidates = ox.features_from_place(
                "Kerala, India",
                tags={"boundary": "administrative", "admin_level": "5"},
            ).reset_index()
            rows = []
            for district in DISTRICTS:
                name_col = candidates.get("name:en", candidates.get("name"))
                if name_col is None:
                    raise ValueError("admin_level=5 response has no district names")
                names = name_col.map(_text)
                matches = candidates[names.str.casefold().eq(district.casefold())]
                matches = matches[matches.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]
                if matches.empty:
                    raise ValueError(f"No admin_level=5 boundary found for {district}")
                rows.append({"name": district, "geometry": unary_union(matches.geometry.tolist())})
        except Exception as fallback_exc:
            raise RuntimeError(
                f"Could not build district AOI; geocoder error={geocode_error!r}; "
                f"admin_level=5 fallback error={fallback_exc!r}"
            ) from fallback_exc

    aoi = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    if set(aoi["name"]) != set(DISTRICTS) or aoi.geometry.is_empty.any():
        raise RuntimeError("AOI must contain valid Ernakulam and Alappuzha polygons")
    CACHE.mkdir(parents=True, exist_ok=True)
    _atomic_vector_write(aoi, path, "GeoJSON")
    _json_write(CACHE / "osm_meta.json", {"retrieved_at": _now(), "aoi_method": "osmnx.geocode_to_gdf"})
    print("AOI cached", flush=True)
    return aoi


def _aoi_union(aoi: gpd.GeoDataFrame):
    return unary_union(aoi.geometry.tolist())


def _feature_frame(
    polygon,
    tags: dict[str, Any],
    *,
    return_source: bool = False,
) -> gpd.GeoDataFrame | tuple[gpd.GeoDataFrame, str]:
    # A bounding-box query is much cheaper for Overpass than serializing the
    # districts' detailed coastlines into a poly query. Callers filter returned
    # geometries against the exact district or AOI geometry.
    bounds = polygon.bounds
    bbox = (bounds[0], bounds[1], bounds[2], bounds[3])
    last_error: Exception | None = None
    for endpoint_index, endpoint in enumerate(OVERPASS_ENDPOINTS):
        ox.settings.overpass_url = endpoint
        for attempt in range(4):
            try:
                frame = ox.features_from_bbox(bbox=bbox, tags=tags).reset_index()
                return (frame, endpoint + "/interpreter") if return_source else frame
            except Exception as exc:
                last_error = exc
                message = str(exc).casefold()
                transient = any(
                    token in message
                    for token in (
                        "429", "502", "503", "504", "timeout", "timed out",
                        "temporarily", "connection reset", "connection aborted",
                        "remote end closed", "server error", "not responding",
                    )
                )
                if transient and attempt < 3:
                    delay = 15 * (2**attempt)
                    print(
                        f"Overpass error at {endpoint}; retrying in {delay}s "
                        f"({attempt + 1}/3): {exc}",
                        flush=True,
                    )
                    time.sleep(delay)
                    continue
                break
        if endpoint_index + 1 < len(OVERPASS_ENDPOINTS):
            print(
                f"Overpass endpoint {endpoint} failed; switching to {OVERPASS_ENDPOINTS[endpoint_index + 1]}",
                flush=True,
            )
    assert last_error is not None
    raise RuntimeError("All configured Overpass endpoints failed") from last_error


def _prepare_taluks(aoi: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    path = LAYERS / "taluks.gpkg"
    if path.exists():
        return gpd.read_file(path)
    print("Phase 2.2: retrieving admin_level=6 taluk boundaries", flush=True)
    aoi_ll = aoi.to_crs("EPSG:4326")
    union_ll = unary_union(aoi_ll.geometry.tolist())
    raw = _feature_frame(union_ll, {"boundary": "administrative", "admin_level": "6"})
    if "admin_level" in raw:
        raw = raw[raw.admin_level.astype(str).eq("6")]
    raw = raw[raw.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    rows = []
    districts = aoi_ll.set_index("name").geometry.to_dict()
    for _, item in raw.iterrows():
        geom = item.geometry
        point = geom.representative_point()
        if not union_ll.covers(point):
            continue
        district = next(
            (name for name in DISTRICTS if districts[name].covers(point)), None
        )
        if district is None:
            continue
        preferred = _text(item.get("name:en")) or _text(item.get("name"))
        if preferred is None:
            continue
        rows.append(
            {
                "name": preferred,
                "name_local": _text(item.get("name:ml")) or _text(item.get("name")),
                "district": district,
                "geometry": geom,
            }
        )
    taluks = gpd.GeoDataFrame(rows, geometry="geometry", crs="EPSG:4326")
    if taluks.empty:
        raise RuntimeError("OSM returned no polygonal admin_level=6 taluks inside the AOI")
    taluks = taluks.drop_duplicates(subset=["district", "name"]).reset_index(drop=True)
    counts = taluks.groupby("district").size().to_dict()
    names = taluks["name"].tolist()
    non_ascii = [name for name in names if not name.isascii()]
    kuttanad = [name for name in names if "kuttanad" in name.casefold()]
    print(f"Taluk counts by district: {counts}", flush=True)
    print(f"Taluk names: {names}", flush=True)
    print(f"Kuttanad matches: {kuttanad}", flush=True)
    if counts != {"Alappuzha": 6, "Ernakulam": 7} or not kuttanad or non_ascii:
        reason = (
            f"OSM taluk verification failed: counts={counts}, Kuttanad={kuttanad}, "
            f"non-ASCII names={non_ascii}. No boundaries were invented."
        )
        raise RuntimeError("NEEDS KIRITO: " + reason)
    taluks = taluks.to_crs(TARGET_CRS)[["name", "name_local", "district", "geometry"]]
    LAYERS.mkdir(parents=True, exist_ok=True)
    _atomic_vector_write(taluks, path, "GPKG")
    print("Taluks verified and cached", flush=True)
    return taluks


def _grid(aoi: gpd.GeoDataFrame) -> tuple[Any, Any, int, int, Any]:
    projected = aoi.to_crs(TARGET_CRS)
    bounds = projected.total_bounds
    left = math.floor(bounds[0] / PIXEL_SIZE) * PIXEL_SIZE
    bottom = math.floor(bounds[1] / PIXEL_SIZE) * PIXEL_SIZE
    right = math.ceil(bounds[2] / PIXEL_SIZE) * PIXEL_SIZE
    top = math.ceil(bounds[3] / PIXEL_SIZE) * PIXEL_SIZE
    width = int(round((right - left) / PIXEL_SIZE))
    height = int(round((top - bottom) / PIXEL_SIZE))
    if width * height >= MAX_PIXELS:
        raise RuntimeError(
            f"Target grid would have {width * height:,} pixels; limit is {MAX_PIXELS:,}"
        )
    transform = from_origin(left, top, PIXEL_SIZE, PIXEL_SIZE)
    union = unary_union(projected.geometry.tolist())
    inside = geometry_mask([mapping(union)], out_shape=(height, width), transform=transform, invert=True)
    return projected, transform, width, height, inside


def _write_raster(path: Path, array: np.ndarray, transform, dtype: str, nodata: Any) -> None:
    temp = path.with_name(path.stem + ".partial" + path.suffix)
    profile = {
        "driver": "GTiff",
        "height": array.shape[0],
        "width": array.shape[1],
        "count": 1,
        "dtype": dtype,
        "crs": TARGET_CRS,
        "transform": transform,
        "nodata": nodata,
        "tiled": True,
        "blockxsize": 512,
        "blockysize": 512,
        "compress": "deflate",
        "predictor": 3 if dtype.startswith("float") else 2,
        "BIGTIFF": "IF_SAFER",
    }
    with rasterio.open(temp, "w", **profile) as dst:
        dst.write(array.astype(dtype, copy=False), 1)
    os.replace(temp, path)


def _stac_items(aoi: gpd.GeoDataFrame) -> tuple[list[Any], list[Any], list[Any]]:
    aoi_ll = aoi.to_crs("EPSG:4326")
    west, south, east, north = aoi_ll.total_bounds
    catalog = Client.open(STAC_URL)
    s1_all = list(
        catalog.search(
            collections=["sentinel-1-rtc"],
            datetime="2018-08-21/2018-08-22",
            bbox=[west, south, east, north],
        ).items()
    )
    s1 = [
        item
        for prefix in EXPECTED_S1_PREFIXES
        for item in s1_all
        if item.id.startswith(prefix) and item.properties.get("sat:orbit_state") == "descending"
    ]
    if len(s1) != 2:
        raise RuntimeError(
            "Expected the two instructed descending S1A slices, found: "
            + ", ".join(item.id for item in s1)
        )
    jrc = list(catalog.search(collections=["jrc-gsw"], bbox=[west, south, east, north]).items())
    jrc = [item for item in jrc if "seasonality" in item.assets]
    dem = list(catalog.search(collections=["cop-dem-glo-30"], bbox=[west, south, east, north]).items())
    dem = [item for item in dem if "data" in item.assets]
    if not jrc or not dem:
        raise RuntimeError(f"STAC search incomplete: JRC={len(jrc)}, DEM={len(dem)}")
    return s1, jrc, dem


def _source_url(item: Any, asset_key: str) -> str:
    signed = pc.sign(item)
    return "/vsicurl/" + signed.assets[asset_key].href


def _sample_rtc_units(item: Any, aoi: gpd.GeoDataFrame) -> tuple[str, dict[str, float]]:
    href = _source_url(item, "vv")
    point = aoi.geometry.union_all().representative_point()
    point = gpd.GeoSeries([point], crs="EPSG:4326").to_crs(TARGET_CRS).iloc[0]
    with rasterio.Env(**GDAL_OPTIONS):
        with rasterio.open(href) as src:
            if src.crs is None:
                raise RuntimeError(f"No CRS in RTC asset {item.id}")
            source_point = gpd.GeoSeries([point], crs=TARGET_CRS).to_crs(src.crs).iloc[0]
            row, col = rowcol(src.transform, source_point.x, source_point.y)
            half = 256
            col0 = max(0, int(col) - half)
            row0 = max(0, int(row) - half)
            window = Window(col0, row0, min(512, src.width - col0), min(512, src.height - row0))
            values = src.read(1, window=window).astype("float32", copy=False)
            valid = np.isfinite(values) & (values != SOURCE_NODATA_S1)
            if src.nodata is not None:
                valid &= values != src.nodata
            sample = values[valid]
            if sample.size < 100:
                # Fall back to small source windows mapped from the district bounds.
                for geom in aoi.to_crs(src.crs).geometry:
                    minx, miny, maxx, maxy = geom.bounds
                    center = ((minx + maxx) / 2, (miny + maxy) / 2)
                    r, c = rowcol(src.transform, *center)
                    c0, r0 = max(0, int(c) - half), max(0, int(r) - half)
                    win = Window(c0, r0, min(512, src.width - c0), min(512, src.height - r0))
                    values = src.read(1, window=win).astype("float32", copy=False)
                    valid = np.isfinite(values) & (values != SOURCE_NODATA_S1)
                    if src.nodata is not None:
                        valid &= values != src.nodata
                    if valid.sum() >= 100:
                        sample = values[valid]
                        break
            if sample.size < 100:
                raise RuntimeError(f"Could not sample valid RTC data from {item.id}")
            # Deterministic decimation bounds memory and avoids a data-dependent random sample.
            sample = sample[:: max(1, sample.size // 100_000)]
            p05, p50, p95 = np.percentile(sample, [5, 50, 95])
    stats = {"p05": float(p05), "p50": float(p50), "p95": float(p95)}
    if 0 < p50 < 2 and 0 <= p05 and p95 < 5:
        units = "linear gamma0"
    elif -40 <= p50 <= 5 and p50 < 0 and p95 <= 10:
        units = "dB"
    else:
        raise RuntimeError(f"RTC units are ambiguous for {item.id}: sample percentiles={stats}")
    return units, stats


def _src_window(src, dst_window: Window, dst_transform) -> Window | None:
    left, bottom, right, top = window_bounds(dst_window, dst_transform)
    left, bottom, right, top = transform_bounds(
        TARGET_CRS, src.crs, left, bottom, right, top, densify_pts=11
    )
    if right <= src.bounds.left or left >= src.bounds.right or top <= src.bounds.bottom or bottom >= src.bounds.top:
        return None
    left, bottom = max(left, src.bounds.left), max(bottom, src.bounds.bottom)
    right, top = min(right, src.bounds.right), min(top, src.bounds.top)
    from rasterio.windows import from_bounds

    guess = from_bounds(left, bottom, right, top, src.transform)
    c0 = max(0, math.floor(guess.col_off) - 3)
    r0 = max(0, math.floor(guess.row_off) - 3)
    c1 = min(src.width, math.ceil(guess.col_off + guess.width) + 3)
    r1 = min(src.height, math.ceil(guess.row_off + guess.height) + 3)
    if c1 <= c0 or r1 <= r0:
        return None
    return Window(c0, r0, c1 - c0, r1 - r0)


def _read_reproject(src, dst_window: Window, dst_transform, resampling, convert_db: bool = False):
    src_window = _src_window(src, dst_window, dst_transform)
    out = np.full((int(dst_window.height), int(dst_window.width)), np.nan, dtype="float32")
    if src_window is None:
        return out
    raw = src.read(1, window=src_window).astype("float32", copy=False)
    valid = src.read_masks(1, window=src_window) > 0
    if src.nodata is not None:
        valid &= raw != src.nodata
    valid &= np.isfinite(raw) & (raw != SOURCE_NODATA_S1) & (raw != 0)
    raw[~valid] = np.nan
    if convert_db:
        raw[valid] = np.power(10.0, raw[valid] / 10.0, dtype="float32")
    reproject(
        source=raw,
        destination=out,
        src_transform=window_transform(src_window, src.transform),
        src_crs=src.crs,
        src_nodata=np.nan,
        dst_transform=window_transform(dst_window, dst_transform),
        dst_crs=TARGET_CRS,
        dst_nodata=np.nan,
        resampling=resampling,
        init_dest_nodata=True,
    )
    return out


def _windows(width: int, height: int):
    for row in range(0, height, TILE):
        for col in range(0, width, TILE):
            yield Window(col, row, min(TILE, width - col), min(TILE, height - row))


def _prepare_s1(
    s1_items,
    aoi,
    transform,
    width,
    height,
    inside,
    *,
    force: bool = False,
) -> tuple[np.ndarray, dict[str, Any]]:
    path = LAYERS / "s1_vv_20180821_db.tif"
    if path.exists() and not force:
        with rasterio.open(path) as src:
            values = src.read(1)
        saved_units = CACHE / "rtc_units.json"
        if saved_units.exists():
            return values, json.loads(saved_units.read_text(encoding="utf-8"))
        units, sample_stats = _sample_rtc_units(s1_items[0], aoi)
        info = {"units": units, "sample_percentiles": sample_stats}
        _json_write(saved_units, info)
        return values, info
    saved_units = CACHE / "rtc_units.json"
    if force and saved_units.exists():
        info = json.loads(saved_units.read_text(encoding="utf-8"))
        units = str(info["units"])
        sample_stats = info["sample_percentiles"]
    else:
        units, sample_stats = _sample_rtc_units(s1_items[0], aoi)
    print(f"RTC units verified: {units}; sample p05/p50/p95={sample_stats}", flush=True)
    total = np.zeros((height, width), dtype="float32")
    count = np.zeros((height, width), dtype="uint8")
    for item in s1_items:
        print(f"Reading signed S1 window stream: {item.id}", flush=True)
        href = _source_url(item, "vv")
        convert_db = units == "dB"
        with rasterio.Env(**GDAL_OPTIONS):
            with rasterio.open(href) as src:
                if src.crs is None:
                    raise RuntimeError(f"No CRS on Sentinel-1 asset {item.id}")
                total_windows = math.ceil(width / TILE) * math.ceil(height / TILE)
                for tile_index, win in enumerate(_windows(width, height), start=1):
                    if tile_index == 1 or tile_index % 5 == 0 or tile_index == total_windows:
                        print(f"S1 window {tile_index}/{total_windows}: {item.id}", flush=True)
                    dest = _read_reproject(src, win, transform, Resampling.average, convert_db)
                    r0, c0 = int(win.row_off), int(win.col_off)
                    r1, c1 = r0 + int(win.height), c0 + int(win.width)
                    region_sum = total[r0:r1, c0:c1]
                    region_count = count[r0:r1, c0:c1]
                    valid = np.isfinite(dest)
                    region_sum[valid] += dest[valid]
                    region_count[valid] += 1
    average = np.full((height, width), np.nan, dtype="float32")
    valid = count > 0
    average[valid] = total[valid] / count[valid]
    # `average` is linear for both source cases: linear input was read directly;
    # dB input was converted to linear before each resampling operation.
    average[valid] = 10.0 * np.log10(np.maximum(average[valid], np.finfo("float32").tiny))
    average[~inside] = np.nan
    _write_raster(path, average, transform, "float32", np.nan)
    info = {"units": units, "sample_percentiles": sample_stats}
    if not (force and saved_units.exists()):
        _json_write(saved_units, info)
    return average, info


def _prepare_continuous_layer(items, key, path, transform, width, height, inside, method):
    full_dem_cache = CACHE / "dem_cop30_full.tif"
    if path.exists():
        if method == "dem" and full_dem_cache.exists():
            with rasterio.open(full_dem_cache) as src:
                return src.read(1)
        with rasterio.open(path) as src:
            return src.read(1)
    fill = NODATA_JRC if method == "jrc" else np.nan
    output = np.full((height, width), fill, dtype="uint8" if method == "jrc" else "float32")
    for item in items:
        print(f"Reading signed {method} window stream: {item.id}", flush=True)
        href = _source_url(item, key)
        with rasterio.Env(**GDAL_OPTIONS):
            with rasterio.open(href) as src:
                for win in _windows(width, height):
                    resampling = Resampling.nearest if method == "jrc" else Resampling.bilinear
                    dest = _read_reproject(src, win, transform, resampling)
                    r0, c0 = int(win.row_off), int(win.col_off)
                    r1, c1 = r0 + int(win.height), c0 + int(win.width)
                    region = output[r0:r1, c0:c1]
                    mask = np.isfinite(dest)
                    if method == "jrc":
                        # Seasonality is categorical; preserve 255 as nodata.
                        mask &= inside[r0:r1, c0:c1]
                        take = mask & (region == NODATA_JRC)
                        region[take] = np.rint(dest[take]).astype("uint8")
                    else:
                        take = mask & ~np.isfinite(region)
                        region[take] = dest[take]
    if method == "jrc":
        output[~inside] = NODATA_JRC
        _write_raster(path, output, transform, "uint8", NODATA_JRC)
    else:
        # Retain an unmasked copy in the ignored cache for boundary-safe slope
        # gradients. The agent-visible DEM remains clipped to the AOI.
        _write_raster(full_dem_cache, output, transform, "float32", np.nan)
        clipped = output.copy()
        clipped[~inside] = np.nan
        _write_raster(path, clipped, transform, "float32", np.nan)
    return output


def _prepare_vector_layers(aoi, aoi_projected, *, force: bool = False):
    LAYERS.mkdir(parents=True, exist_ok=True)
    district_path = LAYERS / "districts.gpkg"
    if not district_path.exists():
        districts = aoi_projected[["name", "geometry"]].copy()
        _atomic_vector_write(districts, district_path, "GPKG")

    aoi_ll = aoi.to_crs("EPSG:4326")
    union_ll = unary_union(aoi_ll.geometry.tolist())
    retrieval_path = CACHE / "osm_retrieval.json"
    retrieval = (
        json.loads(retrieval_path.read_text(encoding="utf-8"))
        if retrieval_path.exists()
        else {"retrieved_at": _now()}
    )
    retrieval.setdefault("layers", {})
    feature_specs = [
        ("hospitals.geojson", {"amenity": "hospital", "healthcare": "hospital"}, "facility"),
        ("schools.geojson", {"amenity": "school"}, "facility"),
        ("roads_major.gpkg", {"highway": ["motorway", "trunk", "primary", "secondary"]}, "roads"),
    ]
    for filename, tags, kind in feature_specs:
        output_path = LAYERS / filename
        if output_path.exists() and not force:
            existing = gpd.read_file(output_path)
            try:
                _validate_vector_layer(existing, filename)
            except ValueError as exc:
                print(f"Rebuilding invalid {filename}: {exc}", flush=True)
            else:
                continue
        print(f"Phase 2.4: retrieving {filename} from OpenStreetMap", flush=True)
        per_district = filename in {"schools.geojson", "roads_major.gpkg"}
        query_areas = (
            [(str(row["name"]), row.geometry) for _, row in aoi_ll.iterrows()]
            if per_district
            else [("AOI", union_ll)]
        )
        frames = []
        endpoints = []
        fetched_rows = 0
        missing_by_element: dict[str, int] = {}
        for district_name, query_area in query_areas:
            if per_district:
                print(f"Querying {filename} for {district_name}", flush=True)
            frame, endpoint = _feature_frame(query_area, tags, return_source=True)
            fetched_rows += len(frame)
            source_missing = frame.geometry.isna() | frame.geometry.is_empty
            if source_missing.any():
                if "element" in frame:
                    counts = frame.loc[source_missing, "element"].fillna("unknown").astype(str).value_counts()
                else:
                    counts = pd.Series({"unknown": int(source_missing.sum())})
                for element, count in counts.items():
                    missing_by_element[element] = missing_by_element.get(element, 0) + int(count)
            frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
            frame = frame[frame.geometry.intersects(query_area)]
            frames.append(frame)
            endpoints.append(endpoint)
        raw = gpd.GeoDataFrame(
            pd.concat(frames, ignore_index=True),
            geometry="geometry",
            crs="EPSG:4326",
        )
        dedupe_columns = [column for column in ("element", "id", "osmid") if column in raw.columns]
        if dedupe_columns:
            raw = raw.drop_duplicates(subset=dedupe_columns).copy()
        raw = raw[raw.geometry.notna() & ~raw.geometry.is_empty].copy()
        raw = raw[raw.geometry.intersects(union_ll)]
        if kind == "facility":
            raw = raw[raw.geometry.geom_type.isin(["Point", "Polygon", "MultiPolygon"])].copy()
            raw = raw.reset_index(drop=True)
            before_save_counts = _element_geometry_counts(raw)
            print(
                f"{filename}: fetched={fetched_rows:,}; dropped missing/empty by element={missing_by_element}; "
                f"pre-save element/geometry counts={before_save_counts}",
                flush=True,
            )
            result = gpd.GeoDataFrame(
                {
                    "osm_id": [_osm_id(row) for _, row in raw.iterrows()],
                    "name": [_text(row.get("name:en")) or _text(row.get("name")) for _, row in raw.iterrows()],
                    "geom_kind": [geom.geom_type for geom in raw.geometry],
                },
                geometry=list(raw.geometry),
                crs="EPSG:4326",
            )
            result = result[["osm_id", "name", "geom_kind", "geometry"]]
            driver = "GeoJSON"
            _atomic_vector_write(result, output_path, driver)
        else:
            raw = raw[raw.geometry.geom_type.eq("LineString")].copy()
            raw = raw.reset_index(drop=True)
            before_save_counts = _element_geometry_counts(raw)
            print(
                f"{filename}: fetched={fetched_rows:,}; dropped missing/empty by element={missing_by_element}; "
                f"pre-save element/geometry counts={before_save_counts}",
                flush=True,
            )
            result = gpd.GeoDataFrame(
                {
                    "highway": [_text(row.get("highway")) for _, row in raw.iterrows()],
                    "name": [_text(row.get("name:en")) or _text(row.get("name")) for _, row in raw.iterrows()],
                },
                geometry=list(raw.geometry),
                crs="EPSG:4326",
            ).to_crs(TARGET_CRS)
            result = result[["highway", "name", "geometry"]]
            driver = "GPKG"
            _atomic_vector_write(result, output_path, driver)
        written = gpd.read_file(output_path)
        written_geometry_counts = _validate_vector_layer(written, filename)
        print(f"Wrote {filename}: {len(written):,} features; geometry counts={written_geometry_counts}", flush=True)
        retrieved_at = _now()
        retrieval["retrieved_at"] = retrieved_at
        retrieval["layers"][filename] = {
            "retrieved_at": retrieved_at,
            "source": "OpenStreetMap Overpass API",
            "endpoints": list(dict.fromkeys(endpoints)),
            "district_queries": [name for name, _ in query_areas if name != "AOI"],
            "fetched_rows": int(fetched_rows),
            "null_or_empty_geometry_dropped_by_element": {str(k): int(v) for k, v in missing_by_element.items()},
            "geometry_counts_before_save_by_element": before_save_counts,
            "geometry_counts_after_save": written_geometry_counts,
            "features_after_save": int(len(written)),
        }
        _json_write(retrieval_path, retrieval)


def _otsu_threshold(values: np.ndarray) -> float:
    hist, edges = np.histogram(
        values,
        bins=VV_HIST_BIN_COUNT,
        range=(VV_HIST_MIN_DB, VV_HIST_MAX_DB),
    )
    return _otsu_from_hist(hist, (edges[:-1] + edges[1:]) / 2.0)


def _round_db_tenth(value: float) -> float:
    """Round to 0.1 dB using conventional half-up rounding, including negatives."""
    return float(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _otsu_from_hist(hist: np.ndarray, centers: np.ndarray) -> float:
    total = int(hist.sum())
    if total == 0:
        raise ValueError("Otsu needs at least one in-range histogram pixel")
    weights = hist.astype("float64") / total
    omega = np.cumsum(weights)
    means = np.cumsum(weights * centers)
    total_mean = means[-1]
    denom = omega * (1.0 - omega)
    between = np.full_like(denom, -np.inf)
    valid = denom > 0
    between[valid] = (total_mean * omega[valid] - means[valid]) ** 2 / denom[valid]
    return float(centers[int(np.argmax(between))])


def _kittler_illingworth(hist: np.ndarray, centers: np.ndarray) -> tuple[float, float]:
    """Return the minimum-error threshold and its criterion value.

    The histogram is split into two Gaussian classes. Minimize
    1 + 2 sum(P_i log(sigma_i)) - 2 sum(P_i log(P_i)).
    """
    counts = hist.astype("float64")
    total = float(counts.sum())
    if total <= 0:
        raise ValueError("Kittler-Illingworth needs histogram pixels")
    p = counts / total
    cumulative = np.cumsum(p)
    first_moment = np.cumsum(p * centers)
    second_moment = np.cumsum(p * centers * centers)
    p_left = cumulative
    p_right = 1.0 - p_left
    safe_left = np.maximum(p_left, np.finfo("float64").tiny)
    safe_right = np.maximum(p_right, np.finfo("float64").tiny)
    mean_left = first_moment / safe_left
    mean_total = first_moment[-1]
    mean_right = (mean_total - first_moment) / safe_right
    variance_left = second_moment / safe_left - mean_left * mean_left
    variance_total = second_moment[-1]
    variance_right = (variance_total - second_moment) / safe_right - mean_right * mean_right
    valid = (p_left > 0) & (p_right > 0) & (variance_left > 0) & (variance_right > 0)
    criterion = np.full_like(p_left, np.inf)
    sigma_left = np.sqrt(np.maximum(variance_left, np.finfo("float64").tiny))
    sigma_right = np.sqrt(np.maximum(variance_right, np.finfo("float64").tiny))
    criterion[valid] = (
        1.0
        + 2.0 * (p_left[valid] * np.log(sigma_left[valid]) + p_right[valid] * np.log(sigma_right[valid]))
        - 2.0 * (p_left[valid] * np.log(p_left[valid]) + p_right[valid] * np.log(p_right[valid]))
    )
    if not np.isfinite(criterion).any():
        raise ValueError("Kittler-Illingworth found no valid two-class split")
    index = int(np.argmin(criterion))
    return float(centers[index]), float(criterion[index])


def _threshold_diagnostics(
    vv: np.ndarray,
    season: np.ndarray,
    inside: np.ndarray,
    projected: gpd.GeoDataFrame,
    transform,
    width: int,
    height: int,
) -> dict[str, Any]:
    edges = np.linspace(VV_HIST_MIN_DB, VV_HIST_MAX_DB, VV_HIST_BIN_COUNT + 1)
    centers = (edges[:-1] + edges[1:]) / 2.0
    valid = inside & np.isfinite(vv) & (vv >= VV_HIST_MIN_DB) & (vv <= VV_HIST_MAX_DB)
    values = vv[valid]
    if values.size == 0:
        raise RuntimeError("No valid in-range VV pixels for threshold diagnosis")
    hist, _ = np.histogram(values, bins=edges)
    t_otsu = _otsu_from_hist(hist, centers)
    t_ki, ki_criterion = _kittler_illingworth(hist, centers)

    smoothed = np.convolve(hist.astype("float64"), np.ones(10, dtype="float64") / 10.0, mode="same")
    water_mode_window = (centers >= -24.0) & (centers <= -14.0)
    land_mode_window = (centers >= -10.0) & (centers <= -1.0)
    if not water_mode_window.any() or not land_mode_window.any():
        raise RuntimeError("Could not locate the expected water and land mode windows")
    water_mode_index = int(np.flatnonzero(water_mode_window)[np.argmax(smoothed[water_mode_window])])
    land_mode_index = int(np.flatnonzero(land_mode_window)[np.argmax(smoothed[land_mode_window])])
    if water_mode_index >= land_mode_index:
        raise RuntimeError("Water mode was not to the left of the land mode")
    valley_index = water_mode_index + int(np.argmin(smoothed[water_mode_index : land_mode_index + 1]))
    t_valley = float(centers[valley_index])
    gate_passed = -22.0 <= t_ki <= -13.0 and abs(t_ki - t_valley) <= 1.5
    threshold = _round_db_tenth(t_valley)

    land_mask = geometry_mask(
        [mapping(unary_union(projected.geometry.tolist()))],
        out_shape=(height, width),
        transform=transform,
        invert=True,
    )
    sea_candidate = valid & ~land_mask
    permanent = valid & (season >= 10) & (season != NODATA_JRC)
    seasonal = valid & (season >= 1) & (season <= 9)
    seasonality_zero = valid & (season == 0)

    def sample_otsu(mask: np.ndarray) -> dict[str, Any] | None:
        sample = vv[mask & valid]
        if sample.size == 0:
            return None
        return {"pixels": int(sample.size), "T_otsu": _otsu_threshold(sample)}

    alt_otsu = {
        "AOI": {"pixels": int(values.size), "T_otsu": t_otsu},
        "excluding_JRC_ge_10": sample_otsu(season < 10),
        "JRC_ge_10": sample_otsu(season >= 10),
        "JRC_1_9": sample_otsu((season >= 1) & (season <= 9)),
        "JRC_0": sample_otsu(season == 0),
    }
    for _, row in projected.iterrows():
        district_mask = geometry_mask(
            [mapping(row.geometry)], out_shape=(height, width), transform=transform, invert=True
        )
        alt_otsu[str(row["name"])] = sample_otsu(district_mask)

    otsu_water_fraction = float(np.count_nonzero(values <= t_otsu) / values.size)
    water_fraction = (
        float(np.count_nonzero(values <= threshold) / values.size) if threshold is not None else None
    )

    histogram_path = CACHE / "vv_histogram.png"
    fig, ax = plt.subplots(figsize=(11, 6.5), constrained_layout=True)
    curves = [
        ("All AOI", valid, "#202a44"),
        ("Sea/outside-land candidate", sea_candidate, "#888888"),
        ("JRC seasonality ≥ 10", permanent, "#1f77b4"),
        ("JRC seasonality 1–9", seasonal, "#e07a2d"),
        ("JRC seasonality 0", seasonality_zero, "#32835a"),
    ]
    for label, mask, color in curves:
        sample = vv[mask]
        if sample.size:
            density, _ = np.histogram(sample, bins=edges, density=True)
            ax.stairs(density, edges, color=color, linewidth=2 if label == "All AOI" else 1.6,
                      label=f"{label} (n={sample.size:,})")
        elif label == "Sea/outside-land candidate":
            ax.plot([], [], color=color, linewidth=1.6, label=f"{label}: no AOI pixels")
    ax.set(title="Sentinel-1 VV dB by JRC seasonality", xlabel="VV backscatter (dB)", ylabel="Probability density")
    ax.set_xlim(VV_HIST_MIN_DB, VV_HIST_MAX_DB)
    ax.grid(alpha=0.22)
    ax.legend(fontsize=9, loc="upper left")
    ax.text(0.99, 0.02, "350 bins at 0.1 dB; non-finite/out-of-range pixels excluded",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"})
    histogram_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(histogram_path, dpi=170)
    plt.close(fig)

    threshold_plot_path = CACHE / "vv_histogram_thresholds.png"
    fig, ax = plt.subplots(figsize=(11, 6.5), constrained_layout=True)
    ax.stairs(hist, edges, color="#202a44", linewidth=1.5, label="AOI pixel count")
    ax.axvline(t_otsu, color="#d62728", linestyle=":", linewidth=2, label=f"T_otsu={t_otsu:.2f} dB")
    ax.axvline(t_ki, color="#1f77b4", linestyle="--", linewidth=2, label=f"T_ki={t_ki:.2f} dB")
    ax.axvline(t_valley, color="#2ca02c", linestyle="-.", linewidth=2, label=f"T_valley={t_valley:.2f} dB")
    ax.axvline(threshold, color="#9467bd", linestyle="-", linewidth=1.8, label=f"Chosen T={threshold:.1f} dB")
    ax.set(title="AOI VV histogram with threshold candidates", xlabel="VV backscatter (dB)", ylabel="Pixel count")
    ax.set_xlim(VV_HIST_MIN_DB, VV_HIST_MAX_DB)
    ax.grid(alpha=0.22)
    ax.legend(loc="upper left")
    fig.savefig(threshold_plot_path, dpi=170)
    plt.close(fig)

    spot_specs = {
        "Vembanad Lake centre": (76.390, 9.600),
        "Central Kochi/MG Road": (76.285, 9.970),
        "Kuttanad paddy near Nedumudi": (76.370, 9.430),
    }
    spots = {}
    for label, (longitude, latitude) in spot_specs.items():
        point = gpd.GeoSeries([Point(longitude, latitude)], crs="EPSG:4326").to_crs(TARGET_CRS).iloc[0]
        spot_mask = geometry_mask([point.buffer(500)], out_shape=(height, width), transform=transform, invert=True)
        spot_values = vv[valid & spot_mask]
        spots[label] = {
            "longitude": longitude,
            "latitude": latitude,
            "radius_m": 500,
            "pixels": int(spot_values.size),
            "median_vv_db": float(np.median(spot_values)) if spot_values.size else None,
        }

    result = {
        "histogram": {"bins": VV_HIST_BIN_COUNT, "bin_width_db": VV_HIST_BIN_WIDTH_DB,
                      "min_db": VV_HIST_MIN_DB, "max_db": VV_HIST_MAX_DB},
        "valid_pixels": int(values.size),
        "T_otsu": t_otsu,
        "T_ki": t_ki,
        "T_valley": t_valley,
        "T": threshold,
        "threshold_choice": {
            "method": "histogram_valley",
            "post_hoc": True,
            "reason": (
                "User-approved post-hoc choice: T_ki failed the range rule by 0.45 dB; "
                "the histogram shows Otsu and KI on the land-mode shoulder, with the "
                "JRC seasonality 1-9 flooded-vegetation tail breaking KI's Gaussian assumption. "
                "T is the 1 dB-smoothed trough between the water and land modes."
            ),
            "sensitivity_db": 1.0,
        },
        "ki_criterion": ki_criterion,
        "water_mode_db": float(centers[water_mode_index]),
        "land_mode_db": float(centers[land_mode_index]),
        "gate_passed": bool(gate_passed),
        "otsu_water_pixel_fraction": otsu_water_fraction,
        "water_pixel_fraction": water_fraction,
        "otsu_alternatives": alt_otsu,
        "sea_candidate_pixels": int(sea_candidate.sum()),
        "spot_medians": spots,
        "histogram_path": str(histogram_path.relative_to(ROOT)),
        "threshold_plot_path": str(threshold_plot_path.relative_to(ROOT)),
    }
    _json_write(CACHE / "threshold_diagnostics.json", result)
    print(f"Threshold histogram: {values.size:,} pixels; {VV_HIST_BIN_COUNT} bins at {VV_HIST_BIN_WIDTH_DB:.1f} dB", flush=True)
    print(f"T_otsu={t_otsu:.4f} dB; T_ki={t_ki:.4f} dB; T_valley={t_valley:.4f} dB; chosen T={threshold:.1f} dB", flush=True)
    print(f"Prior KI rule={'PASS' if gate_passed else 'FAIL'}; post-hoc valley choice; Otsu water fraction={otsu_water_fraction:.6%}; water fraction at T={water_fraction:.6%}", flush=True)
    for name, sample in alt_otsu.items():
        if sample is not None:
            print(f"Otsu {name}: T={sample['T_otsu']:.4f} dB; pixels={sample['pixels']:,}", flush=True)
    for name, entry in spots.items():
        print(f"Spot {name}: median={entry['median_vv_db']} dB; pixels={entry['pixels']:,}", flush=True)
    return result


def _reference_flood(vv, season, dem_full, inside, projected, transform, width, height):
    path = LAYERS / "flood_extent_20180821.gpkg"
    manifest_path = META / "data_manifest.json"
    if path.exists() and manifest_path.exists():
        return gpd.read_file(path), None, None
    thresholds = _threshold_diagnostics(vv, season, inside, projected, transform, width, height)
    valid_vv = inside & np.isfinite(vv)
    threshold_raw = float(thresholds["T_otsu"])
    threshold = float(thresholds["T"])
    print(
        f"T_otsu={threshold_raw:.4f} dB; T_ki={thresholds['T_ki']:.4f} dB; "
        f"T_valley={thresholds['T_valley']:.4f} dB; chosen T={threshold:.1f} dB",
        flush=True,
    )
    water = valid_vv & (vv <= threshold)
    permanent = inside & (season != NODATA_JRC) & (season >= 10)
    valid_dem = inside & np.isfinite(dem_full)
    safe_dem = dem_full.copy()
    safe_dem[~np.isfinite(safe_dem)] = 0.0
    gy, gx = np.gradient(safe_dem, PIXEL_SIZE, PIXEL_SIZE)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    steep = inside & valid_dem & (slope > 5.0)
    flood = water & ~permanent & ~steep & inside
    cache_mask = CACHE / "flood_mask_20180821.tif"
    mask_values = np.full((height, width), 255, dtype="uint8")
    mask_values[inside] = 0
    mask_values[flood] = 1
    _write_raster(cache_mask, mask_values, transform, "uint8", 255)

    geometries = [shape(geom) for geom, value in shapes(
        flood.astype("uint8"), mask=flood, transform=transform, connectivity=8
    ) if value == 1]
    dissolved = unary_union(geometries) if geometries else None
    if dissolved is None or dissolved.is_empty:
        raise RuntimeError("NEEDS KIRITO: KI reference flood is empty")
    flood_gdf = gpd.GeoDataFrame(
        {"source": [f"S1A 2018-08-21 VV histogram valley T={threshold:.1f}"]},
        geometry=[dissolved],
        crs=TARGET_CRS,
    )
    _atomic_vector_write(flood_gdf, path, "GPKG")

    per_district: dict[str, Any] = {}
    counts = {"water": 0, "permanent_water": 0, "steep_ground": 0, "flood": 0}
    district_masks = []
    for _, row in projected.iterrows():
        mask = geometry_mask([mapping(row.geometry)], out_shape=(height, width), transform=transform, invert=True)
        district_masks.append((str(row["name"]), mask))
        part = {
            "water": int(np.count_nonzero(water & mask)),
            "permanent_water": int(np.count_nonzero(permanent & mask)),
            "steep_ground": int(np.count_nonzero(steep & mask)),
            "flood": int(np.count_nonzero(flood & mask)),
        }
        per_district[row["name"]] = {
            key: {"pixels": value, "km2": value * PIXEL_SIZE * PIXEL_SIZE / 1_000_000}
            for key, value in part.items()
        }
        for key, value in part.items():
            counts[key] += value

    taluks = gpd.read_file(LAYERS / "taluks.gpkg").to_crs(TARGET_CRS)
    taluk_masks = []
    pixels_by_taluk: dict[str, Any] = {}
    for _, row in taluks.iterrows():
        mask = geometry_mask([mapping(row.geometry)], out_shape=(height, width), transform=transform, invert=True)
        inside_taluk = mask & inside
        denominator = int(np.count_nonzero(inside_taluk))
        flooded = int(np.count_nonzero(flood & mask))
        name = str(row["name"])
        taluk_masks.append((name, str(row["district"]), inside_taluk))
        pixels_by_taluk[name] = {
            "district": str(row["district"]),
            "aoi_pixels": denominator,
            "flood_pixels": flooded,
            "flood_km2": flooded * PIXEL_SIZE * PIXEL_SIZE / 1_000_000,
            "flooded_percent": 100.0 * flooded / denominator if denominator else 0.0,
        }

    histogram_valid = (
        inside & np.isfinite(vv) & (vv >= VV_HIST_MIN_DB) & (vv <= VV_HIST_MAX_DB)
    )
    histogram_pixel_count = int(np.count_nonzero(histogram_valid))
    sensitivity: dict[str, Any] = {}
    for sensitivity_threshold in (threshold - 1.0, threshold, threshold + 1.0):
        sensitivity_water = valid_vv & (vv <= sensitivity_threshold)
        sensitivity_flood = sensitivity_water & ~permanent & ~steep & inside
        district_sensitivity = {}
        for name, mask in district_masks:
            flooded = int(np.count_nonzero(sensitivity_flood & mask))
            district_sensitivity[name] = {
                "flood_pixels": flooded,
                "flood_km2": flooded * PIXEL_SIZE * PIXEL_SIZE / 1_000_000,
            }
        taluk_sensitivity = {}
        for name, district, mask in taluk_masks:
            flooded = int(np.count_nonzero(sensitivity_flood & mask))
            denominator = int(np.count_nonzero(mask))
            taluk_sensitivity[name] = {
                "district": district,
                "flood_pixels": flooded,
                "flood_km2": flooded * PIXEL_SIZE * PIXEL_SIZE / 1_000_000,
                "flooded_percent": 100.0 * flooded / denominator if denominator else 0.0,
            }
        water_fraction = (
            float(np.count_nonzero(sensitivity_water & histogram_valid) / histogram_pixel_count)
            if histogram_pixel_count else 0.0
        )
        sensitivity[f"{sensitivity_threshold:.1f}"] = {
            "T_db": sensitivity_threshold,
            "water_pixel_fraction": water_fraction,
            "districts": district_sensitivity,
            "taluks": taluk_sensitivity,
        }
    quicklook = CACHE / "quicklook.png"
    stride = max(1, math.ceil(max(width, height) / 1800))
    fig, ax = plt.subplots(figsize=(12, 10), constrained_layout=True)
    vv_view = vv[::stride, ::stride]
    extent = (
        transform.c,
        transform.c + width * PIXEL_SIZE,
        transform.f - height * PIXEL_SIZE,
        transform.f,
    )
    ax.imshow(vv_view, cmap="gray", vmin=-30, vmax=0, interpolation="nearest", extent=extent)
    flood_view = flood[::stride, ::stride]
    perm_view = permanent[::stride, ::stride]
    overlay = np.zeros((*flood_view.shape, 4), dtype="float32")
    overlay[flood_view] = (0.0, 0.3, 1.0, 0.75)
    overlay[perm_view] = (0.0, 0.05, 0.35, 0.85)
    ax.imshow(overlay, interpolation="nearest", extent=extent)
    projected.boundary.plot(ax=ax, color="yellow", linewidth=0.8)
    ax.set_title(f"VV dB with histogram-valley flood (blue), permanent water (navy), T={threshold:.1f} dB")
    ax.set_axis_off()
    quicklook.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(quicklook, dpi=160)
    plt.close(fig)
    result = {
        "T_raw": threshold_raw,
        "T_otsu": threshold_raw,
        "T_ki": thresholds["T_ki"],
        "T_valley": thresholds["T_valley"],
        "T": threshold,
        "threshold_choice": thresholds["threshold_choice"],
        "threshold_diagnostics": thresholds,
        "water_pixel_fraction": thresholds["water_pixel_fraction"],
        "otsu_water_pixel_fraction": thresholds["otsu_water_pixel_fraction"],
        "pixels_by_district": per_district,
        "pixels_by_taluk": pixels_by_taluk,
        "sensitivity_at_plus_minus_1_db": sensitivity,
        "counts_total": counts,
        "total_km2": {key: value * PIXEL_SIZE * PIXEL_SIZE / 1_000_000 for key, value in counts.items()},
    }
    _json_write(CACHE / "flood_stats.json", result)
    return flood_gdf, flood, result


def _nasa_crosscheck(transform, width: int, height: int) -> dict[str, Any]:
    output_path = CACHE / "nasa_compare.png"
    status_path = CACHE / "nasa_crosscheck.json"
    if output_path.is_file() and status_path.is_file():
        existing = json.loads(status_path.read_text(encoding="utf-8"))
        if existing.get("status") == "downloaded":
            return existing
    xmin = float(transform.c)
    ymax = float(transform.f)
    xmax = xmin + width * PIXEL_SIZE
    ymin = ymax - height * PIXEL_SIZE
    out_width = 1200
    out_height = max(1, int(round(out_width * height / width)))
    params = {
        "bbox": f"{xmin},{ymin},{xmax},{ymax}",
        "bboxSR": 32643,
        "size": f"{out_width},{out_height}",
        "imageSR": 32643,
        "format": "png32",
        "transparent": "false",
        "f": "image",
    }
    result: dict[str, Any] = {
        "source": NASA_EXPORT_URL,
        "retrieved_at": _now(),
        "bbox": [xmin, ymin, xmax, ymax],
        "bbox_crs": TARGET_CRS,
        "size": [out_width, out_height],
    }
    try:
        request = Request(
            NASA_EXPORT_URL + "?" + urlencode(params),
            headers={"User-Agent": "KeralaFloodBench/0.1 (NASA map cross-check)"},
        )
        with urlopen(request, timeout=90) as response:
            payload = response.read(25 * 1024 * 1024 + 1)
        if len(payload) > 25 * 1024 * 1024:
            raise RuntimeError("NASA export exceeded the 25 MiB response limit")
        if not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError(f"NASA export did not return PNG bytes: {payload[:160]!r}")
        temp = output_path.with_name(output_path.stem + ".partial" + output_path.suffix)
        temp.write_bytes(payload)
        os.replace(temp, output_path)
        result.update({"status": "downloaded", "path": str(output_path.relative_to(ROOT)), "bytes": len(payload)})
    except Exception as exc:
        result.update({"status": "skipped", "reason": f"{type(exc).__name__}: {exc}"})
    _json_write(status_path, result)
    return result


def _write_manifest(aoi, taluks, stac_items, rtc_info, flood_stats):
    s1_items, jrc_items, dem_items = stac_items
    all_assets = []
    for item, asset_key, collection, acquisition in (
        *((item, "vv", "sentinel-1-rtc", item.properties.get("datetime")) for item in s1_items),
        *((item, "seasonality", "jrc-gsw", item.properties.get("datetime")) for item in jrc_items),
        *((item, "data", "cop-dem-glo-30", item.properties.get("datetime")) for item in dem_items),
    ):
        all_assets.append(
            {
                "collection": collection,
                "item_id": item.id,
                "asset": asset_key,
                "unsigned_href": item.assets[asset_key].href,
                "acquisition_time": acquisition,
            }
        )
    hashes = {name: _sha256(LAYERS / name) for name in EXPECTED_LAYERS}
    feature_counts = {}
    for name in EXPECTED_LAYERS:
        path = LAYERS / name
        if path.suffix.lower() == ".tif":
            with rasterio.open(path) as src:
                feature_counts[name] = {
                    "pixels": int(src.width * src.height),
                    "bands": int(src.count),
                }
        else:
            frame = gpd.read_file(path)
            feature_counts[name] = {
                "features": int(len(frame)),
                "geometry_types": _validate_vector_layer(frame, name),
            }
    with rasterio.open(LAYERS / "s1_vv_20180821_db.tif") as grid_source:
        grid_width, grid_height = grid_source.width, grid_source.height
    osm_retrieval = json.loads((CACHE / "osm_retrieval.json").read_text(encoding="utf-8"))
    manifest = {
        "created_at": _now(),
        "target_grid": {
            "crs": TARGET_CRS,
            "pixel_size_m": PIXEL_SIZE,
            "width": int(grid_width),
            "height": int(grid_height),
        },
        "stac_assets": all_assets,
        "rtc_units_found": rtc_info,
        "T_raw": flood_stats["T_raw"],
        "T_otsu": flood_stats["T_otsu"],
        "T_ki": flood_stats["T_ki"],
        "T_valley": flood_stats["T_valley"],
        "T": flood_stats["T"],
        "threshold_choice": flood_stats["threshold_choice"],
        "water_pixel_fraction": flood_stats["water_pixel_fraction"],
        "otsu_water_pixel_fraction": flood_stats["otsu_water_pixel_fraction"],
        "threshold_diagnostics": flood_stats["threshold_diagnostics"],
        "pixels_and_km2_by_district": flood_stats["pixels_by_district"],
        "pixels_and_km2_by_taluk": flood_stats["pixels_by_taluk"],
        "sensitivity_at_plus_minus_1_db": flood_stats["sensitivity_at_plus_minus_1_db"],
        "pixels_and_km2_total": flood_stats["total_km2"],
        "feature_counts": feature_counts,
        "osm_retrieval_time": osm_retrieval["retrieved_at"],
        "osm_retrieval": osm_retrieval,
        "libraries": {
            "geopandas": gpd.__version__,
            "shapely": __import__("shapely").__version__,
            "rasterio": rasterio.__version__,
            "numpy": np.__version__,
            "osmnx": ox.__version__,
            "pystac_client": __import__("importlib.metadata", fromlist=["version"]).version("pystac-client"),
            "planetary_computer": __import__("importlib.metadata", fromlist=["version"]).version("planetary-computer"),
        },
        "sha256": hashes,
        "taluks": [
            {"name": row["name"], "name_local": row["name_local"], "district": row["district"]}
            for _, row in taluks.iterrows()
        ],
        "optional_nasa_crosscheck": flood_stats.get("optional_nasa_crosscheck", {
            "status": "skipped", "reason": "NASA export was not attempted"
        }),
    }
    _json_write(META / "data_manifest.json", manifest)
    return manifest


def _check() -> None:
    manifest_path = META / "data_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("Missing data\\kerala\\meta\\data_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing = [name for name in EXPECTED_LAYERS if not (LAYERS / name).is_file()]
    if missing:
        raise RuntimeError(f"Missing layers: {missing}")
    for name, crs in EXPECTED_LAYERS.items():
        path = LAYERS / name
        if path.suffix.lower() == ".tif":
            with rasterio.open(path) as src:
                actual = src.crs.to_string() if src.crs else None
                if actual != crs:
                    raise RuntimeError(f"{name}: CRS {actual}, expected {crs}")
                if src.count != 1:
                    raise RuntimeError(f"{name}: expected one raster band, got {src.count}")
                if src.width * src.height >= MAX_PIXELS:
                    raise RuntimeError(f"{name}: {src.width * src.height:,} pixels exceeds limit")
                actual_counts = {"pixels": int(src.width * src.height), "bands": int(src.count)}
        else:
            frame = gpd.read_file(path)
            actual = frame.crs.to_string() if frame.crs else None
            if actual != crs:
                raise RuntimeError(f"{name}: CRS {actual}, expected {crs}")
            try:
                geometry_types = _validate_vector_layer(frame, name)
            except ValueError as exc:
                raise RuntimeError(str(exc)) from exc
            actual_counts = {"features": int(len(frame)), "geometry_types": geometry_types}
        if actual_counts != manifest.get("feature_counts", {}).get(name):
            raise RuntimeError(
                f"{name}: feature counts differ from manifest: "
                f"actual={actual_counts}, recorded={manifest.get('feature_counts', {}).get(name)}"
            )
    threshold = float(manifest["T"])
    if not -22 <= threshold <= -13:
        raise RuntimeError(f"T={threshold} is outside [-22,-13]")
    t_valley = float(manifest["T_valley"])
    choice = manifest.get("threshold_choice", {})
    if choice.get("method") != "histogram_valley" or choice.get("post_hoc") is not True or _round_db_tenth(t_valley) != threshold:
        raise RuntimeError(
            f"Post-hoc valley threshold decision is inconsistent: T_valley={t_valley}, T={threshold}"
        )
    for fraction_name in ("water_pixel_fraction", "otsu_water_pixel_fraction"):
        fraction = float(manifest[fraction_name])
        if not 0.0 <= fraction <= 1.0:
            raise RuntimeError(f"{fraction_name}={fraction} is outside [0,1]")
    flood_km2 = sum(
        district["flood"]["km2"] for district in manifest["pixels_and_km2_by_district"].values()
    )
    aoi_km2 = sum(
        g.area / 1_000_000 for g in gpd.read_file(LAYERS / "districts.gpkg").geometry
    )
    if not 0 < flood_km2 < aoi_km2:
        raise RuntimeError(f"Flood area {flood_km2:.3f} km2 must be >0 and < AOI {aoi_km2:.3f} km2")
    actual_hashes = {name: _sha256(LAYERS / name) for name in EXPECTED_LAYERS}
    if actual_hashes != manifest.get("sha256"):
        raise RuntimeError("Layer SHA-256 hashes do not match data_manifest.json")
    print("Phase 2 data check passed")
    print(
        f"T_otsu={manifest['T_otsu']:.4f} dB; T_ki={manifest['T_ki']:.4f} dB; "
        f"T_valley={t_valley:.4f} dB; T={threshold:.1f} dB"
    )
    print(f"Water pixel fraction at T={manifest['water_pixel_fraction']:.6%}")
    print(f"Flood area={flood_km2:.3f} km2; AOI area={aoi_km2:.3f} km2")
    for name, entry in manifest["pixels_and_km2_by_district"].items():
        print(f"{name}: flood={entry['flood']['km2']:.3f} km2; pixels={entry['flood']['pixels']:,}")
    print("Taluks: " + ", ".join(t["name"] for t in manifest["taluks"]))
    kuttanad = next(
        (entry for name, entry in manifest["pixels_and_km2_by_taluk"].items() if name.casefold() == "kuttanad"),
        None,
    )
    if kuttanad is None:
        raise RuntimeError("Kuttanad taluk is missing from flood statistics")
    print(f"Kuttanad flooded={kuttanad['flooded_percent']:.3f}% ({kuttanad['flood_km2']:.3f} km2)")
    for name, counts in manifest["feature_counts"].items():
        if "geometry_types" in counts:
            print(f"{name}: {counts['features']:,} features; geometry types={counts['geometry_types']}")
        else:
            print(f"{name}: {counts['pixels']:,} pixels; bands={counts['bands']}")
    print(f"Quicklook: {CACHE / 'quicklook.png'}")
    nasa = manifest.get("optional_nasa_crosscheck", {})
    print(f"NASA cross-check: {nasa.get('status', 'not recorded')}; {nasa.get('path', nasa.get('reason', ''))}")
    print(f"Checked {len(EXPECTED_LAYERS)} layers and matching SHA-256 hashes")


def prepare(stage: str = "full") -> None:
    ox.settings.cache_folder = str(CACHE / "osmnx_http")
    ox.settings.http_user_agent = "KeralaFloodBench/0.1 (GISclaw research benchmark; OSM data preparation)"
    ox.settings.requests_timeout = 600
    ox.settings.overpass_url = OVERPASS_ENDPOINTS[0]
    for folder in (LAYERS, META, CACHE):
        folder.mkdir(parents=True, exist_ok=True)
    aoi = _load_aoi()
    if stage == "aoi":
        print("Area of interest ready", flush=True)
        return
    taluks = _prepare_taluks(aoi)
    if stage == "taluks":
        print("Taluks ready", flush=True)
        return
    projected, transform, width, height, inside = _grid(aoi)
    print(f"Target grid EPSG:32643 {width} x {height} = {width * height:,} pixels", flush=True)
    grid_info = {
        "crs": TARGET_CRS, "pixel_size_m": PIXEL_SIZE, "width": width, "height": height,
        "transform": list(transform),
    }
    grid_path = CACHE / "grid.json"
    if not grid_path.exists() or json.loads(grid_path.read_text(encoding="utf-8")) != grid_info:
        _json_write(grid_path, grid_info)
    if stage == "grid":
        print("Target grid cached", flush=True)
        return
    if stage == "vv":
        s1_items = _stac_items(aoi)[0]
        _prepare_s1(s1_items, aoi, transform, width, height, inside, force=True)
        print("VV mosaic rebuilt with nodata, zero and non-finite source samples excluded", flush=True)
        return
    if stage == "vectors":
        _prepare_vector_layers(aoi, projected, force=True)
        print("Vector layers ready", flush=True)
        return
    if stage == "rasters":
        stac_items = _stac_items(aoi)
        s1_items, jrc_items, dem_items = stac_items
        _prepare_s1(s1_items, aoi, transform, width, height, inside)
        _prepare_continuous_layer(
            jrc_items, "seasonality", LAYERS / "jrc_seasonality.tif", transform, width, height, inside, "jrc"
        )
        _prepare_continuous_layer(
            dem_items, "data", LAYERS / "dem_cop30.tif", transform, width, height, inside, "dem"
        )
        print("Raster layers ready", flush=True)
        return
    if stage == "diagnostics":
        with rasterio.open(LAYERS / "s1_vv_20180821_db.tif") as src:
            vv = src.read(1)
        with rasterio.open(LAYERS / "jrc_seasonality.tif") as src:
            season = src.read(1)
        _threshold_diagnostics(vv, season, inside, projected, transform, width, height)
        return
    if stage == "flood":
        with rasterio.open(LAYERS / "s1_vv_20180821_db.tif") as src:
            vv = src.read(1)
        with rasterio.open(LAYERS / "jrc_seasonality.tif") as src:
            season = src.read(1)
        dem_full_path = CACHE / "dem_cop30_full.tif"
        dem_path = dem_full_path if dem_full_path.exists() else LAYERS / "dem_cop30.tif"
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
        _, _, flood_stats = _reference_flood(vv, season, dem, inside, projected, transform, width, height)
        if flood_stats is not None:
            nasa = _nasa_crosscheck(transform, width, height)
            flood_stats["optional_nasa_crosscheck"] = nasa
            _json_write(CACHE / "flood_stats.json", flood_stats)
            print(f"NASA cross-check: {nasa['status']}; {nasa.get('path', nasa.get('reason', ''))}", flush=True)
        print("Reference flood and quicklook ready", flush=True)
        return
    if stage == "manifest":
        manifest_path = META / "data_manifest.json"
        if manifest_path.exists():
            _check()
            return
        stac_items = _stac_items(aoi)
        rtc_info = json.loads((CACHE / "rtc_units.json").read_text(encoding="utf-8"))
        flood_stats = json.loads((CACHE / "flood_stats.json").read_text(encoding="utf-8"))
        flood_stats.setdefault("optional_nasa_crosscheck", _nasa_crosscheck(transform, width, height))
        _json_write(CACHE / "flood_stats.json", flood_stats)
        _write_manifest(aoi, taluks, stac_items, rtc_info, flood_stats)
        print("Manifest written", flush=True)
        return

    _prepare_vector_layers(aoi, projected)
    stac_items = _stac_items(aoi)
    s1_items, jrc_items, dem_items = stac_items
    vv, rtc_info = _prepare_s1(s1_items, aoi, transform, width, height, inside)
    season = _prepare_continuous_layer(
        jrc_items, "seasonality", LAYERS / "jrc_seasonality.tif", transform, width, height, inside, "jrc"
    )
    dem_full = _prepare_continuous_layer(
        dem_items, "data", LAYERS / "dem_cop30.tif", transform, width, height, inside, "dem"
    )
    # Slope uses valid Copernicus DEM values on the full target rectangle. The stored raster is clipped.
    flood_gdf, flood_mask, flood_stats = _reference_flood(
        vv, season, dem_full, inside, projected, transform, width, height
    )
    if flood_stats is None:
        # A complete manifest is the resumability marker; no new data should be fabricated from it.
        print("Reference flood and manifest already exist; checking hashes", flush=True)
        _check()
        return
    nasa = _nasa_crosscheck(transform, width, height)
    flood_stats["optional_nasa_crosscheck"] = nasa
    _json_write(CACHE / "flood_stats.json", flood_stats)
    _write_manifest(aoi, taluks, stac_items, rtc_info, flood_stats)
    print("Phase 2 layers and manifest written", flush=True)
    print(f"NASA cross-check: {nasa['status']}; {nasa.get('path', nasa.get('reason', ''))}", flush=True)
    for name, info in flood_stats["pixels_by_district"].items():
        print(f"{name}: flood={info['flood']['km2']:.3f} km2", flush=True)
    for name, info in flood_stats["pixels_by_taluk"].items():
        if name.casefold() == "kuttanad":
            print(f"{name}: flood={info['flood_km2']:.3f} km2 ({info['flooded_percent']:.3f}% of in-AOI taluk pixels)", flush=True)
    print("Taluks: " + ", ".join(taluks["name"].tolist()), flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check prepared layers and manifest hashes")
    parser.add_argument(
        "--stage",
        choices=["full", "aoi", "taluks", "grid", "vectors", "rasters", "vv", "diagnostics", "flood", "manifest"],
        default="full",
        help="run one resumable preparation stage (default: full)",
    )
    args = parser.parse_args(argv)
    try:
        if args.check:
            _check()
        else:
            prepare(args.stage)
    except Exception as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
