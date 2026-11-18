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


_src = rasterio.open('dataset/s1_vv_20180821_db.tif')
if _src.count > 1:
    vv = _src.read().astype(float)
else:
    vv = _src.read(1).astype(float)
vv_meta = dict(
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
    print(f"Shape: {vv.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = vv[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: vv has {_src.count} bands. Access bands by index: vv[0]=Band1, vv[1]=Band2, etc.")
else:
    print(f"Value range: min={vv.min():.4g}, max={vv.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    vv[vv == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={vv[~_np.isnan(vv)].min():.4g}, max={vv[~_np.isnan(vv)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: vv is ndarray(float) shape (H, W), vv_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=vv.shape[0], width=vv.shape[1], count=1, dtype='float32', crs=vv_meta['crs'], transform=vv_meta['transform'])")
_src.close()


_src = rasterio.open('dataset/jrc_seasonality.tif')
if _src.count > 1:
    season = _src.read().astype(float)
else:
    season = _src.read(1).astype(float)
season_meta = dict(
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
    print(f"Shape: {season.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = season[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: season has {_src.count} bands. Access bands by index: season[0]=Band1, season[1]=Band2, etc.")
else:
    print(f"Value range: min={season.min():.4g}, max={season.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    season[season == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={season[~_np.isnan(season)].min():.4g}, max={season[~_np.isnan(season)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: season is ndarray(float) shape (H, W), season_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=season.shape[0], width=season.shape[1], count=1, dtype='float32', crs=season_meta['crs'], transform=season_meta['transform'])")
_src.close()


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
import rasterio.crs as _rio_crs
_meta = dict(dem_meta)
if _meta.get('crs') is not None and _rio_crs.CRS.from_user_input(_meta['crs']).is_geographic:
    print('❌ The DEM must be reprojected to a projected CRS before calculating slope.')
else:
    _arr = dem.astype(float)
    _px = abs(_meta['transform'].a); _py = abs(_meta['transform'].e)
    _dy, _dx = _np.gradient(_arr * 1, _py, _px)
    slope_dem = _np.degrees(_np.arctan(_np.sqrt(_dx**2 + _dy**2))).astype('float32')
    slope_dem_meta = _meta
    import rasterio as _rio
    _m = slope_dem_meta
    with _rio.open('pred_results/slope_dem.tif', 'w', driver='GTiff', height=slope_dem.shape[-2], width=slope_dem.shape[-1], count=1, dtype='float32', crs=_m['crs'], transform=_m['transform'], nodata=_m.get('nodata')) as _dst:
        _dst.write(slope_dem.astype('float32'), 1)
    print(f'OK slope_dem: raster {slope_dem.shape}, EPSG:{_m["crs"].to_epsg() if _m["crs"] else None}')


import json, numpy as np, rasterio, geopandas as gpd
from rasterio.mask import mask

# Geometry of Kuttanad taluk
kuttanad = taluks[taluks['name'] == 'Kuttanad'].to_crs(vv_meta['crs'])
geom = [kuttanad.geometry.unary_union]

# Clip Sentinel‑1 VV
with rasterio.open('dataset/s1_vv_20180821_db.tif') as vv_ds:
    vv_clip, vv_tr = mask(vv_ds, geom, crop=True, nodata=np.nan)
    vv_arr = vv_clip[0]

# Clip JRC seasonality (nodata 255)
with rasterio.open('dataset/jrc_seasonality.tif') as sea_ds:
    sea_clip, _ = mask(sea_ds, geom, crop=True, nodata=255)
    sea_arr = sea_clip[0]

# Clip DEM and compute slope on clipped DEM
with rasterio.open('dataset/dem_cop30.tif') as dem_ds:
    dem_clip, _ = mask(dem_ds, geom, crop=True, nodata=np.nan)
    dem_arr = dem_clip[0]
    # compute slope in degrees
    x, y = np.gradient(dem_arr, dem_ds.res[0], dem_ds.res[1])
    slp_arr = np.degrees(np.arctan(np.sqrt(x**2 + y**2)))

# Apply masks
flood_mask = (vv_arr < -14.0) & (~np.isnan(vv_arr))
water_mask = (sea_arr >= 10) & (~np.isnan(sea_arr))
steep_mask = (slp_arr > 5.0) & (~np.isnan(slp_arr))
final_mask = flood_mask & (~water_mask) & (~steep_mask)

pixel_count = np.count_nonzero(final_mask)
flooded_area = pixel_count * 900  # m^2

# Taluk area (in m^2)
taluk_area = kuttanad.geometry.area.iloc[0]
percent = (flooded_area / taluk_area) * 100

answer = {
    "question_id": "P07",
    "status": "ok",
    "value": round(percent, 2),
    "unit": "percent",
    "parameters_used": {
        "water_threshold_vv_db": -14.0,
        "permanent_water_rule": "jrc_seasonality >= 10",
        "max_flood_slope_deg": 5,
        "raster_area_rule": "pixel_count * 900 m2"
    },
    "assumptions": "All rasters are aligned and use the same CRS; pixel centre rule applies.",
    "method": "Raster clipping, masking, and pixel counting to compute flooded area percentage."
}

with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)


import os
os.makedirs('pred_results', exist_ok=True)
_saved = []
# current matplotlib figure
try:
    import matplotlib.pyplot as plt
    if plt.get_fignums():
        plt.savefig('pred_results/emergency_plot.png', dpi=150, bbox_inches='tight')
        _saved.append('emergency_plot.png')
except: pass
# largest GeoDataFrame
try:
    import geopandas as _gpd
    _gdf_candidates = []
    for _n, _v in list(globals().items()):
        if isinstance(_v, _gpd.GeoDataFrame) and len(_v) > 0 and not _n.startswith('_'):
            _gdf_candidates.append((_n, _v))
    if _gdf_candidates:
        _name, _gdf = max(_gdf_candidates, key=lambda x: len(x[1]))
        _gdf.to_file('pred_results/emergency_output.geojson', driver='GeoJSON')
        _saved.append(f'{_name}.geojson')
except: pass
# largest DataFrame
try:
    import pandas as _pd
    _df_candidates = []
    for _n, _v in list(globals().items()):
        if isinstance(_v, _pd.DataFrame) and not isinstance(_v, _gpd.GeoDataFrame) and len(_v) > 0 and not _n.startswith('_'):
            _df_candidates.append((_n, _v))
    if _df_candidates:
        _name, _df = max(_df_candidates, key=lambda x: len(x[1]))
        _df.to_csv('pred_results/emergency_output.csv', index=False)
        _saved.append(f'{_name}.csv')
except: pass
print(f'Emergency save: {_saved}')
