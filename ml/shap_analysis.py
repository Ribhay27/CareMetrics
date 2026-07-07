from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from common.config import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"


def _to_2d_shap(values):
    arr = np.array(values)
    if arr.ndim == 3:
        arr = np.mean(np.abs(arr), axis=2)
    return arr


def save_shap_values(model_bundle_path: Path, output_parquet: Path, output_png: Path, label: str) -> None:
    bundle = joblib.load(model_bundle_path)
    model = bundle["model"]
    feature_cols = bundle["feature_columns"]
    df = pd.read_parquet(PROCESSED / "features.parquet")
    X = df[feature_cols]
    sample = X.sample(min(len(X), 5000), random_state=42) if len(X) > 5000 else X
    explainer = shap.TreeExplainer(model)
    values = explainer.shap_values(sample)
    shap_2d = _to_2d_shap(values)
    out = pd.DataFrame(shap_2d, columns=feature_cols)
    out.insert(0, "provider_id", df.loc[sample.index, "provider_id"].values)
    out.to_parquet(output_parquet, index=False)

    shap.summary_plot(values, sample, plot_type="bar", show=False, max_display=15)
    plt.tight_layout()
    plt.savefig(output_png, dpi=160, bbox_inches="tight")
    plt.close()
    importance = pd.Series(np.abs(shap_2d).mean(axis=0), index=feature_cols).sort_values(ascending=False).head(10)
    print(f"\nTop 10 {label} SHAP features")
    print(importance.to_string())
    print(f"Saved {output_parquet}")
    print(f"Saved {output_png}")


def main() -> int:
    save_shap_values(MODEL_DIR / "readmission_classifier.pkl", PROCESSED / "shap_classifier.parquet", PROCESSED / "shap_classifier_summary.png", "classifier")
    save_shap_values(MODEL_DIR / "quality_regressor.pkl", PROCESSED / "shap_regressor.parquet", PROCESSED / "shap_regressor_summary.png", "regressor")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
