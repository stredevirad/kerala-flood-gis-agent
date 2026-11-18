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


hospitals = gpd.read_file('dataset/hospitals.geojson')
print(f"Rows: {len(hospitals)}")
print(f"CRS: {hospitals.crs}")
print(f"Columns: {list(hospitals.columns)}")
print()
# Show first 3 rows
print(hospitals.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in hospitals.columns if c != 'geometry'][:6]:
    try:
        uniques = hospitals[col].dropna().unique()
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
_b = districts.to_crs(hospitals_utm.crs) if (hospitals_utm.crs is not None and districts.crs is not None and hospitals_utm.crs != districts.crs) else districts
hospitals_with_district = _gpd.sjoin(hospitals_utm, _b, predicate='within', how='left')
_disp_write(hospitals_with_district, 'hospitals_with_district')
_summ(hospitals_with_district, 'hospitals_with_district')



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
hospitals_with_district = hospitals_with_district.copy()
hospitals_with_district['is_ernakulam'] = hospitals_with_district.eval("name_right=='Ernakulam'")
_disp_write(hospitals_with_district, 'hospitals_with_district')
_summ(hospitals_with_district, 'hospitals_with_district')


import json, os
# Count hospitals in Ernakulam
count = hospitals_with_district[hospitals_with_district['is_ernakulam']].shape[0]
answer = {
  "question_id": "C04",
  "status": "ok",
  "value": int(count),
  "unit": "count",
  "parameters_used": {},
  "assumptions": "Assumes district name field is 'name' and hospitals are points.",
  "method": "Spatial join of hospitals to districts and count where district name is Ernakulam."
}
# ensure output directory exists
os.makedirs('pred_results', exist_ok=True)
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print(count)