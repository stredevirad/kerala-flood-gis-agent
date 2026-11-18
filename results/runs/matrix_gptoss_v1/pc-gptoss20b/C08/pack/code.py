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


import json
answer = {
  "question_id": "C08",
  "status": "cannot_answer",
  "value": None,
  "unit": None,
  "parameters_used": {},
  "assumptions": "No evacuation data available in the provided datasets.",
  "method": "Checked all available layers for evacuation count fields; none found."
}
with open("pred_results/answer.json", "w", encoding="utf-8") as f:
    json.dump(answer, f, ensure_ascii=False, indent=2)
