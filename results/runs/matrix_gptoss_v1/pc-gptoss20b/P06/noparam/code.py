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


_src = rasterio.open('dataset/jrc_seasonality.tif')
if _src.count > 1:
    jrc = _src.read().astype(float)
else:
    jrc = _src.read(1).astype(float)
jrc_meta = dict(
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
    print(f"Shape: {jrc.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = jrc[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: jrc has {_src.count} bands. Access bands by index: jrc[0]=Band1, jrc[1]=Band2, etc.")
else:
    print(f"Value range: min={jrc.min():.4g}, max={jrc.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    jrc[jrc == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={jrc[~_np.isnan(jrc)].min():.4g}, max={jrc[~_np.isnan(jrc)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: jrc is ndarray(float) shape (H, W), jrc_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=jrc.shape[0], width=jrc.shape[1], count=1, dtype='float32', crs=jrc_meta['crs'], transform=jrc_meta['transform'])")
_src.close()


_src = rasterio.open('dataset/dem_cop30.tif')
if _src.count > 1:
    dem_cop30 = _src.read().astype(float)
else:
    dem_cop30 = _src.read(1).astype(float)
dem_cop30_meta = dict(
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
    print(f"Shape: {dem_cop30.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = dem_cop30[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: dem_cop30 has {_src.count} bands. Access bands by index: dem_cop30[0]=Band1, dem_cop30[1]=Band2, etc.")
else:
    print(f"Value range: min={dem_cop30.min():.4g}, max={dem_cop30.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    dem_cop30[dem_cop30 == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={dem_cop30[~_np.isnan(dem_cop30)].min():.4g}, max={dem_cop30[~_np.isnan(dem_cop30)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: dem_cop30 is ndarray(float) shape (H, W), dem_cop30_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=dem_cop30.shape[0], width=dem_cop30.shape[1], count=1, dtype='float32', crs=dem_cop30_meta['crs'], transform=dem_cop30_meta['transform'])")
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
_meta = dict(dem_cop30_meta)
if _meta.get('crs') is not None and _rio_crs.CRS.from_user_input(_meta['crs']).is_geographic:
    print('❌ The DEM must be reprojected to a projected CRS before calculating slope.')
else:
    _arr = dem_cop30.astype(float)
    _px = abs(_meta['transform'].a); _py = abs(_meta['transform'].e)
    _dy, _dx = _np.gradient(_arr * 1, _py, _px)
    slope = _np.degrees(_np.arctan(_np.sqrt(_dx**2 + _dy**2))).astype('float32')
    slope_meta = _meta
    import rasterio as _rio
    _m = slope_meta
    with _rio.open('pred_results/slope.tif', 'w', driver='GTiff', height=slope.shape[-2], width=slope.shape[-1], count=1, dtype='float32', crs=_m['crs'], transform=_m['transform'], nodata=_m.get('nodata')) as _dst:
        _dst.write(slope.astype('float32'), 1)
    print(f'OK slope: raster {slope.shape}, EPSG:{_m["crs"].to_epsg() if _m["crs"] else None}')


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
