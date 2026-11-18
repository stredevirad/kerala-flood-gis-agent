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
