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
_m = districts.to_crs(flood.crs) if (flood.crs is not None and districts.crs is not None and flood.crs != districts.crs) else districts
flood_ernakulam = _gpd.clip(flood, _m)
_disp_write(flood_ernakulam, 'flood_ernakulam')
_summ(flood_ernakulam, 'flood_ernakulam')
try:
    flood_ernakulam.to_file('pred_results/flood_ernakulam.geojson', driver='GeoJSON' if 'pred_results/flood_ernakulam.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_ernakulam.geojson')
except Exception as _e:
    print('save failed:', _e)


import geopandas as gpd
area_m2 = flood_ernakulam.geometry.area.sum()
area_km2 = area_m2/1e6
area_km2


import json
answer = {
  "question_id": "C06",
  "status": "ok",
  "value": 336.46560204636177,
  "unit": "km2",
  "parameters_used": {},
  "assumptions": "Flood extent polygon is already in the district CRS and represents flooded area accurately.",
  "method": "Clip flood extent to Ernakulam district and sum area of resulting geometry."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print("written")