from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import explained_variance_score, mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, KFold, train_test_split
from tabulate import tabulate

from common.config import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    df = pd.read_parquet(PROCESSED / "features.parquet")
    y = pd.to_numeric(df["composite_quality_score"], errors="coerce").fillna(df["composite_quality_score"].median())
    exclude = {"provider_id", "hospital_name", "city", "state", "readmission_risk_label", "quality_tier", "composite_quality_score"}
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
    X = df[feature_cols]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LGBMRegressor(random_state=42, n_jobs=2)
    param_grid = {
        "num_leaves": [31, 50, 70],
        "learning_rate": [0.05, 0.1],
        "n_estimators": [100, 200],
        "min_child_samples": [20, 30],
    }
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(model, param_grid, cv=cv, scoring="neg_root_mean_squared_error", n_jobs=2, verbose=1)
    grid.fit(X_train, y_train)
    best = grid.best_estimator_
    pred = best.predict(X_test)

    metrics = {
        "best_params": grid.best_params_,
        "cv_best_rmse": float(-grid.best_score_),
        "rmse": float(np.sqrt(mean_squared_error(y_test, pred))),
        "mae": float(mean_absolute_error(y_test, pred)),
        "r2": float(r2_score(y_test, pred)),
        "explained_variance": float(explained_variance_score(y_test, pred)),
        "feature_columns": feature_cols,
    }
    joblib.dump({"model": best, "feature_columns": feature_cols}, MODEL_DIR / "quality_regressor.pkl")
    (PROCESSED / "regressor_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(tabulate([[k, v] for k, v in metrics.items() if isinstance(v, (int, float))], headers=["metric", "value"], tablefmt="github", floatfmt=".4f"))
    print(f"Saved {MODEL_DIR / 'quality_regressor.pkl'}")
    print(f"Saved {PROCESSED / 'regressor_metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
