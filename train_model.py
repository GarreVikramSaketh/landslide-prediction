"""
train_model.py
Trains & evaluates multiple classifiers, then saves the best model.
Run:  python train_model.py
"""

import pandas as pd
import numpy as np
import pickle, os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection    import train_test_split, cross_val_score
from sklearn.ensemble           import RandomForestClassifier, GradientBoostingClassifier
from sklearn.tree               import DecisionTreeClassifier
from sklearn.linear_model       import LogisticRegression
from sklearn.preprocessing      import StandardScaler
from sklearn.metrics            import (accuracy_score, classification_report,
                                        confusion_matrix, roc_auc_score,
                                        ConfusionMatrixDisplay)

# ── Load data ────────────────────────────────────────────────────────────────
df = pd.read_csv("dataset.csv")
FEATURES = ["rainfall_24h_mm","weekly_rainfall_mm","slope_degrees",
            "elevation_m","soil_type","vegetation_cover","soil_moisture_pct"]
TARGET   = "landslide"

X = df[FEATURES]
y = df[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ── Define models ─────────────────────────────────────────────────────────────
models = {
    "Random Forest":          RandomForestClassifier(n_estimators=200, max_depth=12,
                                                     random_state=42, n_jobs=-1),
    "Gradient Boosting":      GradientBoostingClassifier(n_estimators=150,
                                                         learning_rate=0.1,
                                                         max_depth=5, random_state=42),
    "Decision Tree":          DecisionTreeClassifier(max_depth=10, random_state=42),
    "Logistic Regression":    LogisticRegression(max_iter=1000, random_state=42),
}

results = {}
print("\n─── Model Comparison ───────────────────────────────────")
for name, model in models.items():
    use_scaled = name in ("Logistic Regression",)
    Xtr = X_train_s if use_scaled else X_train
    Xte = X_test_s  if use_scaled else X_test

    model.fit(Xtr, y_train)
    preds  = model.predict(Xte)
    acc    = accuracy_score(y_test, preds)
    auc    = roc_auc_score(y_test, model.predict_proba(Xte)[:,1])
    cv     = cross_val_score(model, Xtr, y_train, cv=5, scoring="accuracy").mean()
    results[name] = {"accuracy": acc, "auc": auc, "cv_accuracy": cv}
    print(f"  {name:<25}  Acc={acc:.4f}  AUC={auc:.4f}  CV={cv:.4f}")

# ── Best model (prefer tree-based for explainability + real-world reliability) ─
# Logistic Regression can over-report AUC on synthetic data; we compare RF vs GB
tree_models = {k: v for k, v in results.items() if k in ("Random Forest", "Gradient Boosting")}
best_name = max(tree_models, key=lambda k: tree_models[k]["auc"])
best_model = models[best_name]
# Re-fit to ensure it was trained on unscaled data
best_model.fit(X_train, y_train)
print(f"\n🏆 Best model: {best_name}")
print(classification_report(y_test, best_model.predict(X_test), target_names=["Safe","Landslide"]))

# ── Save artefacts ────────────────────────────────────────────────────────────
os.makedirs("model", exist_ok=True)
with open("model/model.pkl",   "wb") as f: pickle.dump(best_model, f)
with open("model/scaler.pkl",  "wb") as f: pickle.dump(scaler, f)
with open("model/features.json","w") as f: json.dump(FEATURES, f)
with open("model/results.json", "w") as f: json.dump(results, f)
print("✅  Saved → model/model.pkl  |  model/scaler.pkl")

# ── Plots ─────────────────────────────────────────────────────────────────────
os.makedirs("static", exist_ok=True)

# 1. Accuracy comparison bar
fig, ax = plt.subplots(figsize=(8, 4))
names  = list(results.keys())
accs   = [results[n]["accuracy"]*100 for n in names]
colors = ["#e74c3c" if n == best_name else "#3498db" for n in names]
bars   = ax.barh(names, accs, color=colors, edgecolor="white", height=0.55)
for bar, v in zip(bars, accs):
    ax.text(v + 0.3, bar.get_y() + bar.get_height()/2,
            f"{v:.1f}%", va="center", fontsize=10, color="#2c3e50")
ax.set_xlim(50, 105)
ax.set_xlabel("Accuracy (%)", fontsize=11)
ax.set_title("Model Accuracy Comparison", fontsize=13, fontweight="bold")
ax.spines[["top","right"]].set_visible(False)
plt.tight_layout()
plt.savefig("static/model_comparison.png", dpi=120, bbox_inches="tight")
plt.close()

# 2. Feature importance (Random Forest / GBM)
if hasattr(best_model, "feature_importances_"):
    fi = pd.Series(best_model.feature_importances_, index=FEATURES).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    fi.plot(kind="barh", ax=ax, color="#e74c3c", edgecolor="white")
    ax.set_title("Feature Importance", fontsize=13, fontweight="bold")
    ax.set_xlabel("Importance Score")
    ax.spines[["top","right"]].set_visible(False)
    plt.tight_layout()
    plt.savefig("static/feature_importance.png", dpi=120, bbox_inches="tight")
    plt.close()

# 3. Confusion matrix
cm   = confusion_matrix(y_test, best_model.predict(X_test))
disp = ConfusionMatrixDisplay(cm, display_labels=["Safe","Landslide"])
fig, ax = plt.subplots(figsize=(5, 4))
disp.plot(ax=ax, colorbar=False, cmap="Reds")
ax.set_title("Confusion Matrix", fontsize=13, fontweight="bold")
plt.tight_layout()
plt.savefig("static/confusion_matrix.png", dpi=120, bbox_inches="tight")
plt.close()

print("✅  Charts saved to static/")
print("\nTraining complete 🎉")
