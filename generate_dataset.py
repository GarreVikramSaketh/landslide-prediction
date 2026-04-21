"""
generate_dataset.py
Generates a realistic synthetic landslide dataset and saves it as CSV.
Run this ONCE before training: python generate_dataset.py
"""

import numpy as np
import pandas as pd

np.random.seed(42)
N = 2000

# ── Feature generation ──────────────────────────────────────────────────────
rainfall_24h  = np.random.uniform(0, 300, N)      # mm
weekly_rain   = np.random.uniform(0, 800, N)       # mm
slope         = np.random.uniform(5, 70, N)        # degrees
elevation     = np.random.uniform(100, 3000, N)    # metres
soil_type     = np.random.choice([0, 1, 2, 3], N)  # 0=clay,1=sandy,2=loam,3=rocky
vegetation    = np.random.uniform(0, 1, N)         # cover index 0-1
moisture      = np.random.uniform(10, 100, N)      # %

# ── Physics-inspired labelling ───────────────────────────────────────────────
# Risk score: high rainfall + steep slope + clay/sandy soil = danger
soil_risk = np.where(soil_type == 0, 1.4,          # clay  – worst
            np.where(soil_type == 1, 1.2,          # sandy
            np.where(soil_type == 2, 1.0,          # loam
                                     0.6)))        # rocky – best

risk_score = (
    (rainfall_24h / 300)  * 3.0 +
    (weekly_rain  / 800)  * 2.0 +
    (slope        / 70)   * 3.5 +
    (moisture     / 100)  * 1.5 +
    soil_risk             * 1.5 -
    vegetation            * 1.0
)

threshold = np.percentile(risk_score, 62)          # ~38 % positive rate
landslide = (risk_score > threshold).astype(int)

# Add a touch of noise (real world is messy)
flip_idx = np.random.choice(N, size=int(N * 0.04), replace=False)
landslide[flip_idx] = 1 - landslide[flip_idx]

df = pd.DataFrame({
    "rainfall_24h_mm":  np.round(rainfall_24h, 2),
    "weekly_rainfall_mm": np.round(weekly_rain, 2),
    "slope_degrees":    np.round(slope, 2),
    "elevation_m":      np.round(elevation, 2),
    "soil_type":        soil_type,          # 0=clay,1=sandy,2=loam,3=rocky
    "vegetation_cover": np.round(vegetation, 3),
    "soil_moisture_pct": np.round(moisture, 2),
    "landslide":        landslide
})

df.to_csv("dataset.csv", index=False)
print(f"✅  Dataset saved: dataset.csv  ({N} rows, {landslide.sum()} landslide events)")
print(df.head())
