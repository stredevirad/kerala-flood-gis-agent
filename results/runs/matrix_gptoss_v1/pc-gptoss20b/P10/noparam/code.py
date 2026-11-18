import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.warp import reproject, calculate_default_transform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon, MultiPolygon, box
from shapely.ops import unary_union
import warnings
warnings.filterwarnings('ignore')
os.makedirs('pred_results', exist_ok=True)


taluks = gpd.read_file('dataset/taluks.gpkg')
print(f"Rows: {len(taluks)}")
print(f"CRS: {taluks.crs}")
print(f"Columns: {list(taluks.columns)}")
print()
# Show first 3 rows
print(taluks.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in taluks.columns if c != 'geometry'][:6]:
    try:
        uniques = taluks[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass



import os as _os, numpy as _np, geopandas as _gpd, pandas as _pd
_os.makedirs('pred_results', exist_ok=True)
def _disp_write(_g, _name):
    # Write a WGS84 GeoJSON snapshot for auto-render on the map.
    try:
        _d = _g
        if getattr(_d, 'crs', None) is not None:
            _d = _d.to_crs(4326)
        _d.to_file('pred_results/' + _name + '.geojson', driver='GeoJSON')
    except Exception:
        pass
def _summ(_g, _label):
    try:
        _crs = _g.crs.to_epsg() if getattr(_g, 'crs', None) is not None else None
        print(f"OK {_label}: {len(_g)} features, EPSG:{_crs}")
    except Exception:
        print(f"OK {_label}")
_src = taluks
_geo = (_src.crs is None) or _src.crs.is_geographic
_work = _src.to_crs(_src.estimate_utm_crs()) if _geo else _src
taluks_buffered = _work.copy()
taluks_buffered['geometry'] = _work.geometry.buffer(0)
taluks_buffered = taluks_buffered.to_crs(_src.crs) if _geo and _src.crs is not None else taluks_buffered
_disp_write(taluks_buffered, 'taluks_buffered')
_summ(taluks_buffered, 'taluks_buffered')


flood = gpd.read_file('dataset/flood_extent_20180821.gpkg')
print(f"Rows: {len(flood)}")
print(f"CRS: {flood.crs}")
print(f"Columns: {list(flood.columns)}")
print()
# Show first 3 rows
print(flood.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in flood.columns if c != 'geometry'][:6]:
    try:
        uniques = flood[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


import json, os, numpy as np, rasterio
from rasterio.features import rasterize
from shapely.geometry import mapping

# Load data
with rasterio.open("dataset/dem_cop30.tif") as src:
    dem = src.read(1)
    profile = src.profile
    transform = src.transform

# Parameters
low_lying_max_elevation_m = 5.0
raster_area_rule = 10.0  # km²

# Create low‑lying mask
low_mask = np.where(dem <= low_lying_max_elevation_m, 1, 0).astype(rasterio.uint8)

# Rasterize taluks
import geopandas as gpd

taluks = gpd.read_file("dataset/taluks.gpkg")
# assign integer id
taluks = taluks.copy()
taluks['id'] = range(1, len(taluks)+1)
geom_tuples = [(geom, val) for geom, val in zip(taluks.geometry, taluks.id)]
taluk_raster = rasterize(geom_tuples, out_shape=dem.shape, transform=transform, fill=0, dtype=rasterio.uint16)

# Rasterize flood extent
flood = gpd.read_file("dataset/flood_extent_20180821.gpkg")
flood_geom = [(geom, 1) for geom in flood.geometry]
flood_raster = rasterize(flood_geom, out_shape=dem.shape, transform=transform, fill=0, dtype=rasterio.uint8)

# Pixel area in km²
pixel_area_km2 = (transform.a * -transform.e) / 1e6  # 30*30

# Compute low‑lying area per taluk
low_area = {}
for tid in np.unique(taluk_raster):
    if tid == 0:
        continue
    mask = (taluk_raster == tid) & (low_mask == 1)
    low_area[tid] = mask.sum() * pixel_area_km2

# Compute overlap area with flood
overlap_area = {}
for tid in np.unique(taluk_raster):
    if tid == 0:
        continue
    mask = (taluk_raster == tid) & (low_mask == 1) & (flood_raster == 1)
    overlap_area[tid] = mask.sum() * pixel_area_km2

# Compute share for taluks meeting area rule
share = {}
for tid, area in low_area.items():
    if area >= raster_area_rule:
        share[tid] = (overlap_area.get(tid, 0) / area) * 100

# Find taluk with maximum share
if share:
    max_tid = max(share, key=share.get)
    max_share = share[max_tid]
    max_name = taluks.loc[taluks.id == max_tid, 'name'].values[0]
else:
    max_tid = None
    max_share = None
    max_name = None

# Prepare answer dictionary
answer = {
    "question_id": "P10",
    "status": "ok" if max_share is not None else "cannot_answer",
    "value": round(max_share, 2) if max_share is not None else None,
    "unit": "percent",
    "parameters_used": {
        "low_lying_max_elevation_m": low_lying_max_elevation_m,
        "raster_area_rule": raster_area_rule
    },
    "assumptions": f"Low‑lying defined as elevation ≤ {low_lying_max_elevation_m} m and only taluks with ≥{raster_area_rule} km² of such land considered.",
    "method": "Rasterized taluk and flood layers, computed low‑lying area and overlap, then selected taluk with highest percentage overlap."
}

# Write output
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)

print("Answer written to pred_results/answer.json")


import os
os.makedirs('pred_results', exist_ok=True)
print('Contents of pred_results:', os.listdir('pred_results'))

import json, os, numpy as np, rasterio
from rasterio.features import rasterize
import geopandas as gpd

# Load data
with rasterio.open("dataset/dem_cop30.tif") as src:
    dem = src.read(1)
    profile = src.profile
    transform = src.transform

# Parameters
low_lying_max_elevation_m = 5.0
raster_area_rule = 10.0  # km²

# Create low‑lying mask
low_mask = np.where(dem <= low_lying_max_elevation_m, 1, 0).astype(rasterio.uint8)

# Rasterize taluks
taluks = gpd.read_file("dataset/taluks.gpkg")
taluks = taluks.copy()
taluks["id"] = range(1, len(taluks)+1)
geom_tuples = [(geom, val) for geom, val in zip(taluks.geometry, taluks.id)]
taluk_raster = rasterize(geom_tuples, out_shape=dem.shape, transform=transform, fill=0, dtype=rasterio.uint16)

# Rasterize flood extent
flood = gpd.read_file("dataset/flood_extent_20180821.gpkg")
flood_geom = [(geom, 1) for geom in flood.geometry]
flood_raster = rasterize(flood_geom, out_shape=dem.shape, transform=transform, fill=0, dtype=rasterio.uint8)

# Pixel area in km²
pixel_area_km2 = (transform.a * -transform.e) / 1e6  # 30*30

# Compute low‑lying area per taluk
low_area = {}
for tid in np.unique(taluk_raster):
    if tid == 0:
        continue
    mask = (taluk_raster == tid) & (low_mask == 1)
    low_area[tid] = mask.sum() * pixel_area_km2

# Compute overlap area with flood
overlap_area = {}
for tid in np.unique(taluk_raster):
    if tid == 0:
        continue
    mask = (taluk_raster == tid) & (low_mask == 1) & (flood_raster == 1)
    overlap_area[tid] = mask.sum() * pixel_area_km2

# Compute share for taluks meeting area rule
share = {}
for tid, area in low_area.items():
    if area >= raster_area_rule:
        share[tid] = (overlap_area.get(tid, 0) / area) * 100

# Find taluk with maximum share
if share:
    max_tid = max(share, key=share.get)
    max_name = taluks.loc[taluks.id == max_tid, "name"].values[0]
else:
    max_name = None

# Prepare answer dictionary
answer = {
    "question_id": "P10",
    "status": "ok" if max_name is not None else "cannot_answer",
    "value": max_name,
    "unit": "name",
    "parameters_used": {
        "low_lying_max_elevation_m": low_lying_max_elevation_m,
        "raster_area_rule": raster_area_rule
    },
    "assumptions": f"Low‑lying defined as elevation ≤ {low_lying_max_elevation_m} m and only taluks with ≥{raster_area_rule} km² of such land considered.",
    "method": "Rasterized taluk and flood layers, computed low‑lying area and overlap, then selected taluk with highest percentage overlap."
}

# Write output
os.makedirs("pred_results", exist_ok=True)
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)

print("Answer written to pred_results/answer.json")
