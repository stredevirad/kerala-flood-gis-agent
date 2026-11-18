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


flood_extent = gpd.read_file('dataset/flood_extent_20180821.gpkg')
print(f"Rows: {len(flood_extent)}")
print(f"CRS: {flood_extent.crs}")
print(f"Columns: {list(flood_extent.columns)}")
print()
# Show first 3 rows
print(flood_extent.head(3).to_string())
print()
# Show unique values for key columns
for col in [c for c in flood_extent.columns if c != 'geometry'][:6]:
    try:
        uniques = flood_extent[col].dropna().unique()
        if len(uniques) <= 10:
            print(f"{col} unique values: {list(uniques)}")
        else:
            print(f"{col}: {len(uniques)} unique values, e.g.: {list(uniques[:5])}")
    except:
        pass


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
hospitals_utm = hospitals.to_crs('EPSG:32643')
_disp_write(hospitals_utm, 'hospitals_utm')
_summ(hospitals_utm, 'hospitals_utm')



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
_src = hospitals_utm
_geo = (_src.crs is None) or _src.crs.is_geographic
_work = _src.to_crs(_src.estimate_utm_crs()) if _geo else _src
hospitals_buf = _work.copy()
hospitals_buf['geometry'] = _work.geometry.buffer(100)
hospitals_buf = hospitals_buf.to_crs(_src.crs) if _geo and _src.crs is not None else hospitals_buf
_disp_write(hospitals_buf, 'hospitals_buf')
_summ(hospitals_buf, 'hospitals_buf')



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
_b = flood_extent.to_crs(hospitals_buf.crs) if (hospitals_buf.crs is not None and flood_extent.crs is not None and hospitals_buf.crs != flood_extent.crs) else flood_extent
hospitals_flooded = _gpd.overlay(hospitals_buf, _b, how='intersection')
_disp_write(hospitals_flooded, 'hospitals_flooded')
_summ(hospitals_flooded, 'hospitals_flooded')



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
_b = districts.to_crs(hospitals_flooded.crs) if (hospitals_flooded.crs is not None and districts.crs is not None and hospitals_flooded.crs != districts.crs) else districts
hospitals_flooded_alappuzha = _gpd.overlay(hospitals_flooded, _b, how='intersection')
_disp_write(hospitals_flooded_alappuzha, 'hospitals_flooded_alappuzha')
_summ(hospitals_flooded_alappuzha, 'hospitals_flooded_alappuzha')


import pandas as pd
count = hospitals_flooded_alappuzha['osm_id'].nunique()
count


import json
answer = {
  "question_id": "P01",
  "status": "ok",
  "value": 82,
  "unit": "count",
  "parameters_used": {
    "facility_point_rule": "buffer",
    "facility_flood_buffer_m": 100
  },
  "assumptions": "A 100 m buffer around each hospital point was used to represent the facility flood buffer.",
  "method": "Buffer hospitals by 100 m, intersect with flood extent, then intersect with Alappuzha district and count unique hospitals."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
