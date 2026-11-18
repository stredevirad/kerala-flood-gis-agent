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


import json
# Compute area of Alappuzha district
alappuzha = districts[districts['name'] == 'Alappuzha']
area_m2 = alappuzha.geometry.area.iloc[0]
area_km2 = area_m2 / 1e6
answer = {
    "question_id": "C01",
    "status": "ok",
    "value": round(area_km2, 2),
    "unit": "km2",
    "parameters_used": {},
    "assumptions": "Area computed from the provided district polygon in EPSG:32643.",
    "method": "Polygon area in projected CRS, converted to km²."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)


import os
print(os.listdir('pred_results/'))
