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


_src = rasterio.open('dataset/jrc_seasonality.tif')
if _src.count > 1:
    seasonality = _src.read().astype(float)
else:
    seasonality = _src.read(1).astype(float)
seasonality_meta = dict(
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
    print(f"Shape: {seasonality.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = seasonality[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: seasonality has {_src.count} bands. Access bands by index: seasonality[0]=Band1, seasonality[1]=Band2, etc.")
else:
    print(f"Value range: min={seasonality.min():.4g}, max={seasonality.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    seasonality[seasonality == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={seasonality[~_np.isnan(seasonality)].min():.4g}, max={seasonality[~_np.isnan(seasonality)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: seasonality is ndarray(float) shape (H, W), seasonality_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=seasonality.shape[0], width=seasonality.shape[1], count=1, dtype='float32', crs=seasonality_meta['crs'], transform=seasonality_meta['transform'])")
_src.close()


_src = rasterio.open('dataset/jrc_seasonality.tif')
if _src.count > 1:
    seasonality = _src.read().astype(float)
else:
    seasonality = _src.read(1).astype(float)
seasonality_meta = dict(
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
    print(f"Shape: {seasonality.shape} (bands, height, width)")
    for _b in range(_src.count):
        _band = seasonality[_b]
        print(f"  Band {_b+1}: min={_band[~__import__('numpy').isnan(_band)].min():.4g}, max={_band[~__import__('numpy').isnan(_band)].max():.4g}" if not __import__('numpy').all(__import__('numpy').isnan(_band)) else f"  Band {_b+1}: all NaN")
    print(f"\nHint: seasonality has {_src.count} bands. Access bands by index: seasonality[0]=Band1, seasonality[1]=Band2, etc.")
else:
    print(f"Value range: min={seasonality.min():.4g}, max={seasonality.max():.4g}")
print(f"Bounds: {_src.bounds}")
if _src.nodata is not None:
    print(f"NoData: {_src.nodata}")
    import numpy as _np
    seasonality[seasonality == _src.nodata] = _np.nan
    if _src.count == 1:
        print(f"NoData replaced with NaN, valid range: min={seasonality[~_np.isnan(seasonality)].min():.4g}, max={seasonality[~_np.isnan(seasonality)].max():.4g}")
    else:
        print(f"NoData replaced with NaN across all bands")
print(f"Transform: {_src.transform}")
if _src.count == 1:
    print(f"\\nHint: seasonality is ndarray(float) shape (H, W), seasonality_meta is dict(crs/transform/nodata etc.)")
    print(f"To write GeoTIFF: rasterio.open(path, 'w', driver='GTiff', height=seasonality.shape[0], width=seasonality.shape[1], count=1, dtype='float32', crs=seasonality_meta['crs'], transform=seasonality_meta['transform'])")
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
