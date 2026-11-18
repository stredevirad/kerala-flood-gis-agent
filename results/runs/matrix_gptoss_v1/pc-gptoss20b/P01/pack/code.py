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
_src = flood_extent
_geo = (_src.crs is None) or _src.crs.is_geographic
_work = _src.to_crs(_src.estimate_utm_crs()) if _geo else _src
flood_buffer = _work.copy()
flood_buffer['geometry'] = _work.geometry.buffer(0)
flood_buffer = flood_buffer.to_crs(_src.crs) if _geo and _src.crs is not None else flood_buffer
_disp_write(flood_buffer, 'flood_buffer')
_summ(flood_buffer, 'flood_buffer')
try:
    flood_buffer.to_file('pred_results/flood_buffer.geojson', driver='GeoJSON' if 'pred_results/flood_buffer.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_buffer.geojson')
except Exception as _e:
    print('save failed:', _e)



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
_src = flood_extent
_geo = (_src.crs is None) or _src.crs.is_geographic
_work = _src.to_crs(_src.estimate_utm_crs()) if _geo else _src
flood_buffer_250 = _work.copy()
flood_buffer_250['geometry'] = _work.geometry.buffer(250)
flood_buffer_250 = flood_buffer_250.to_crs(_src.crs) if _geo and _src.crs is not None else flood_buffer_250
_disp_write(flood_buffer_250, 'flood_buffer_250')
_summ(flood_buffer_250, 'flood_buffer_250')
try:
    flood_buffer_250.to_file('pred_results/flood_buffer_250.geojson', driver='GeoJSON' if 'pred_results/flood_buffer_250.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_buffer_250.geojson')
except Exception as _e:
    print('save failed:', _e)



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
_m = districts.to_crs(flood_buffer_250.crs) if (flood_buffer_250.crs is not None and districts.crs is not None and flood_buffer_250.crs != districts.crs) else districts
flood_buffer_alappuzha = _gpd.clip(flood_buffer_250, _m)
_disp_write(flood_buffer_alappuzha, 'flood_buffer_alappuzha')
_summ(flood_buffer_alappuzha, 'flood_buffer_alappuzha')
try:
    flood_buffer_alappuzha.to_file('pred_results/flood_buffer_alappuzha.geojson', driver='GeoJSON' if 'pred_results/flood_buffer_alappuzha.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/flood_buffer_alappuzha.geojson')
except Exception as _e:
    print('save failed:', _e)



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
_b = flood_buffer_alappuzha.to_crs(hospitals_utm.crs) if (hospitals_utm.crs is not None and flood_buffer_alappuzha.crs is not None and hospitals_utm.crs != flood_buffer_alappuzha.crs) else flood_buffer_alappuzha
hospitals_within_flood = _gpd.sjoin(hospitals_utm, _b, predicate='within', how='left')
_disp_write(hospitals_within_flood, 'hospitals_within_flood')
_summ(hospitals_within_flood, 'hospitals_within_flood')
try:
    hospitals_within_flood.to_file('pred_results/hospitals_within_flood.geojson', driver='GeoJSON' if 'pred_results/hospitals_within_flood.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/hospitals_within_flood.geojson')
except Exception as _e:
    print('save failed:', _e)



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
hospitals_in_flood = hospitals_within_flood.query('source.notna()').reset_index(drop=True)
_disp_write(hospitals_in_flood, 'hospitals_in_flood')
_summ(hospitals_in_flood, 'hospitals_in_flood')
try:
    hospitals_in_flood.to_file('pred_results/hospitals_in_flood.geojson', driver='GeoJSON' if 'pred_results/hospitals_in_flood.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/hospitals_in_flood.geojson')
except Exception as _e:
    print('save failed:', _e)


import json
count = len(hospitals_in_flood)
answer = {
  "question_id": "P01",
  "status": "ok",
  "value": count,
  "unit": "count",
  "parameters_used": {"facility_flood_buffer_m": 250, "facility_point_rule": "representative_point"},
  "assumptions": "All hospitals are represented by point geometries and the 250 m buffer captures flood‑affected facilities.",
  "method": "Buffer flood extent, clip to Alappuzha, spatial join with hospitals, count points inside."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
print(count)