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
kuttanad = taluks.query("name == 'Kuttanad'").reset_index(drop=True)
_disp_write(kuttanad, 'kuttanad')
_summ(kuttanad, 'kuttanad')
