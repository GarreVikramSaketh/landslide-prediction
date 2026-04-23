"""
app.py  –  Flask web application for Landslide Prediction
Run:  python app.py
Then open:  http://127.0.0.1:5000
"""

from flask import Flask, render_template, request, jsonify
import pickle, json
import numpy as np

app = Flask(__name__)

# ── Load model artefacts ──────────────────────────────────────────────────────
with open("model/model.pkl",    "rb") as f: MODEL   = pickle.load(f)
with open("model/scaler.pkl",   "rb") as f: SCALER  = pickle.load(f)
with open("model/features.json","r") as f: FEATURES = json.load(f)
with open("model/results.json", "r") as f: RESULTS  = json.load(f)

SOIL_LABELS = {0: "Clay", 1: "Sandy", 2: "Loam", 3: "Rocky"}

@app.route("/")
def index():
    best = max(RESULTS, key=lambda k: RESULTS[k]["auc"])
    stats = {
        "best_model": best,
        "accuracy":   round(RESULTS[best]["accuracy"] * 100, 2),
        "auc":        round(RESULTS[best]["auc"] * 100, 2),
        "models":     {k: {"acc": round(v["accuracy"]*100, 2),
                           "auc": round(v["auc"]*100, 2)}
                       for k, v in RESULTS.items()}
    }
    return render_template("index.html", stats=stats)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()

        rainfall_24h   = float(data["rainfall_24h"])
        weekly_rain    = float(data["weekly_rain"])
        slope          = float(data["slope"])
        elevation      = float(data["elevation"])
        soil_type      = int(data["soil_type"])
        vegetation     = float(data["vegetation"]) / 100   # UI sends 0-100
        moisture       = float(data["moisture"])

        features = np.array([[rainfall_24h, weekly_rain, slope,
                               elevation, soil_type, vegetation, moisture]])

        prob   = MODEL.predict_proba(features)[0][1]
        label  = int(MODEL.predict(features)[0])

        # Risk level
        if prob >= 0.75:
            risk_level = "CRITICAL"
            risk_color = "#c0392b"
        elif prob >= 0.50:
            risk_level = "HIGH"
            risk_color = "#e67e22"
        elif prob >= 0.30:
            risk_level = "MODERATE"
            risk_color = "#f1c40f"
        else:
            risk_level = "LOW"
            risk_color = "#27ae60"

        # Contributing factors
        factors = []
        if rainfall_24h > 100:  factors.append(f"Heavy 24h rainfall ({rainfall_24h} mm)")
        if weekly_rain  > 350:  factors.append(f"High weekly accumulation ({weekly_rain} mm)")
        if slope        > 35:   factors.append(f"Steep slope ({slope}°)")
        if moisture     > 70:   factors.append(f"High soil moisture ({moisture}%)")
        if soil_type    in (0,1): factors.append(f"{SOIL_LABELS[soil_type]} soil (unstable)")
        if not factors:         factors = ["Conditions are within safe range"]

        return jsonify({
            "label":      label,
            "probability": round(prob * 100, 1),
            "risk_level": risk_level,
            "risk_color": risk_color,
            "factors":    factors,
            "soil_name":  SOIL_LABELS[soil_type]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
