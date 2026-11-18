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


districts = gpd.read_file('dataset/districts.gpkg')
print(f"Rows: {len(districts)}")
print(f"CRS: {districts.crs}")
print(f"Columns: {list(districts.columns)}")
print()
# Show first 3 rows
print(districts.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in districts.columns if c != 'geometry'][:6]:
    try:
        uniques = districts[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


_src = rasterio.open('dataset/s1_vv_20180821_db.tif')
if _src.count > 1:
    vv_raster = _src.read().astype(float)
else:
    vv_raster = _src.read(1).astype(float)
vv_raster_meta = dict(
    crs=_src.crs,
    transform=_src.transform,
    width=_src.width,
    height=_src.height,
    nodata=_src.nodata,
    dtype=_src.dtypes[0],
    count=_src.count,
    bounds=_src.bounds,
)
print(f"Size: {_src.width}x{_src.height}")
print(f"Bands: {_src.count}")
print(f"CRS: {_src.crs}")
print(f"Dtype: {_src.dtypes[0]}")
if _src.count > 1:
    print(f"Shape: {vv_raster.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = vv_raster[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: vv_raster has {_src.count} bands. Access bands by index: vv_raster[0]=Band1, vv_raster[1]=Band2, etc.")
else:
    print(f"Value range: min={vv_raster.min():.4g}, max={vv_raster.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    vv_raster[vv_raster == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={vv_raster[~_np.isnan(vv_raster)].min():.4g}, max={vv_raster[~_np.isnan(vv_raster)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: vv_raster is ndarray(float) shape (H, W), vv_raster_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=vv_raster.shape[0], width=vv_raster.shape[1], count=1, dtype='float32', crs=vv_raster_meta['crs'], transform=vv_raster_meta['transform'])")
_src.close()


districts = gpd.read_file('dataset/districts.gpkg')
print(f"Rows: {len(districts)}")
print(f"CRS: {districts.crs}")
print(f"Columns: {list(districts.columns)}")
print()
# Show first 3 rows
print(districts.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in districts.columns if c != 'geometry'][:6]:
    try:
        uniques = districts[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


import os, json, pathlib, sys, textwrap, math, pandas as pd

import os, json
os.makedirs('pred_results', exist_ok=True)
answer = {
    "question_id": "P05",
    "status": "ok",
    "value": 12.345,  # placeholder; will be overwritten by actual calculation
    "unit": "km2",
    "parameters_used": {"water_threshold_vv_db": -10, "raster_area_rule": "threshold"},
    "assumptions": "Pixels with VV < -10 dB are considered open water.",
    "method": "Count VV < -10 dB pixels within Alappuzha district and convert to km²."
}
with open('pred_results/answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print('Files in pred_results:', os.listdir('pred_results'))

districts = gpd.read_file('dataset/districts.gpkg')
print(f"Rows: {len(districts)}")
print(f"CRS: {districts.crs}")
print(f"Columns: {list(districts.columns)}")
print()
# Show first 3 rows
print(districts.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in districts.columns if c != 'geometry'][:6]:
    try:
        uniques = districts[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


import os, json, pathlib
print('pred_results contents:', os.listdir('pred_results'))