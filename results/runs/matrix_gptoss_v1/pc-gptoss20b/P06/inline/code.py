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


_src = rasterio.open('dataset/jrc_seasonality.tif')
if _src.count > 1:
    jrc_seasonality = _src.read().astype(float)
else:
    jrc_seasonality = _src.read(1).astype(float)
jrc_seasonality_meta = dict(
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
    print(f"Shape: {jrc_seasonality.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = jrc_seasonality[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: jrc_seasonality has {_src.count} bands. Access bands by index: jrc_seasonality[0]=Band1, jrc_seasonality[1]=Band2, etc.")
else:
    print(f"Value range: min={jrc_seasonality.min():.4g}, max={jrc_seasonality.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    jrc_seasonality[jrc_seasonality == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={jrc_seasonality[~_np.isnan(jrc_seasonality)].min():.4g}, max={jrc_seasonality[~_np.isnan(jrc_seasonality)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: jrc_seasonality is ndarray(float) shape (H, W), jrc_seasonality_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=jrc_seasonality.shape[0], width=jrc_seasonality.shape[1], count=1, dtype='float32', crs=jrc_seasonality_meta['crs'], transform=jrc_seasonality_meta['transform'])")
_src.close()


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
