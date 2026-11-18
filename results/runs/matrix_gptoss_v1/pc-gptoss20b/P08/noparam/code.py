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
alappuzha = districts.query("name == 'Alappuzha'").reset_index(drop=True)
_disp_write(alappuzha, 'alappuzha')
_summ(alappuzha, 'alappuzha')
try:
    alappuzha.to_file('pred_results/alappuzha.geojson', driver='GeoJSON' if 'pred_results/alappuzha.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/alappuzha.geojson')
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
_m = flood_extent.to_crs(alappuzha.crs) if (alappuzha.crs is not None and flood_extent.crs is not None and alappuzha.crs != flood_extent.crs) else flood_extent
alappuzha_flood = _gpd.clip(alappuzha, _m)
_disp_write(alappuzha_flood, 'alappuzha_flood')
_summ(alappuzha_flood, 'alappuzha_flood')
try:
    alappuzha_flood.to_file('pred_results/alappuzha_flood.geojson', driver='GeoJSON' if 'pred_results/alappuzha_flood.geojson'.endswith('.geojson') else None)
    print('saved -> ' + 'pred_results/alappuzha_flood.geojson')
except Exception as _e:
    print('save failed:', _e)


_src = rasterio.open('dataset/dem_cop30.tif')
if _src.count > 1:
    dem = _src.read().astype(float)
else:
    dem = _src.read(1).astype(float)
dem_meta = dict(
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
    print(f"Shape: {dem.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = dem[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: dem has {_src.count} bands. Access bands by index: dem[0]=Band1, dem[1]=Band2, etc.")
else:
    print(f"Value range: min={dem.min():.4g}, max={dem.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    dem[dem == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={dem[~_np.isnan(dem)].min():.4g}, max={dem[~_np.isnan(dem)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: dem is ndarray(float) shape (H, W), dem_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=dem.shape[0], width=dem.shape[1], count=1, dtype='float32', crs=dem_meta['crs'], transform=dem_meta['transform'])")
_src.close()



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
import rasterio as _rio
from rasterio.features import geometry_mask as _gm
_arr = dem; _meta = dict(dem_meta)
_mk = alappuzha_flood.to_crs(_meta['crs']) if (alappuzha_flood.crs is not None and _meta['crs'] is not None and alappuzha_flood.crs != _meta['crs']) else alappuzha_flood
_mask = _gm(_mk.geometry, out_shape=_arr.shape[-2:], transform=_meta['transform'], invert=True)
dem_clip = _np.where(_mask, _arr, _np.nan).astype('float32')
dem_clip_meta = _meta
import rasterio as _rio
_m = dem_clip_meta
with _rio.open('pred_results/dem_clip.tif', 'w', driver='GTiff', height=dem_clip.shape[-2], width=dem_clip.shape[-1], count=1, dtype='float32', crs=_m['crs'], transform=_m['transform'], nodata=_m.get('nodata')) as _dst:
    _dst.write(dem_clip.astype('float32'), 1)
print(f'OK dem_clip: raster {dem_clip.shape}, EPSG:{_m["crs"].to_epsg() if _m["crs"] else None}')


import numpy as np, json, os, rasterio, geopandas as gpd, pandas as pd, matplotlib.pyplot as plt
# dem_clip array and meta already in env
# mask polygon already clipped; but we have dem_clip array with NaNs outside mask
low_thresh=5.0
mask = ~np.isnan(dem_clip)
low = (dem_clip < low_thresh) & mask
count = int(low.sum())
area_km2 = count*900/1e6
answer = {
  "question_id":"P08",
  "status":"ok",
  "value":area_km2,
  "unit":"km2",
  "parameters_used":{"low_lying_max_elevation_m":5,"raster_area_rule":"pixel_area"},
  "assumptions":"Assumed low‑lying as elevation <5 m and used 30 m pixel size.",
  "method":"Count DEM cells <5 m within Alappuzha flood extent and convert to km²."
}
with open("pred_results/answer.json","w",encoding="utf-8") as f:
    json.dump(answer,f,ensure_ascii=False,indent=2)
print("count",count,"area",area_km2)
