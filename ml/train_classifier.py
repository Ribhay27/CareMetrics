from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score, classification_report
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import LabelEncoder, label_binarize
from tabulate import tabulate
from xgboost import XGBClassifier

from common.config import PROJECT_ROOT

PROCESSED = PROJECT_ROOT / "data" / "processed"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def main() -> int:
    df = pd.read_parquet(PROCESSED / "features.parquet")
    if "readmission_risk_label" not in df:
        raise RuntimeError("features.parquet does not contain readmission_risk_label")
    y_text = df["readmission_risk_label"].astype(str).fillna("Medium")
    encoder = LabelEncoder()
    y = encoder.fit_transform(y_text)

    exclude = {"provider_id", "hospital_name", "city", "state", "readmission_risk_label", "quality_tier"}
    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in exclude]
    X = df[feature_cols]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = XGBClassifier(objective="multi:softprob", eval_metric="mlogloss", random_state=42, n_jobs=2)
    param_grid = {
        "max_depth": [3, 5, 7],
        "n_estimators": [100, 200],
        "learning_rate": [0.05, 0.1],
        "subsample": [0.8, 1.0],
    }
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    grid = GridSearchCV(model, param_grid, cv=cv, scoring="f1_macro", n_jobs=2, verbose=1)
    grid.fit(X_train, y_train)
    best = grid.best_estimator_

    proba = best.predict_proba(X_test)
    pred = best.predict(X_test)
    classes = list(encoder.classes_)
    y_bin = label_binarize(y_test, classes=list(range(len(classes))))
    auc = roc_auc_score(y_bin, proba, average="macro", multi_class="ovr") if len(classes) > 2 else roc_auc_score(y_test, proba[:, 1])

    metrics = {
        "best_params": grid.best_params_,
        "cv_best_score_f1_macro": float(grid.best_score_),
        "auc_roc_macro": float(auc),
        "classes": classes,
        "feature_columns": feature_cols,
        "f1_per_class": dict(zip(classes, f1_score(y_test, pred, average=None).astype(float))),
        "precision_per_class": dict(zip(classes, precision_score(y_test, pred, average=None, zero_division=0).astype(float))),
        "recall_per_class": dict(zip(classes, recall_score(y_test, pred, average=None, zero_division=0).astype(float))),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }
    joblib.dump({"model": best, "label_encoder": encoder, "feature_columns": feature_cols}, MODEL_DIR / "readmission_classifier.pkl")
    (PROCESSED / "classifier_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    rows = [["AUC-ROC macro", metrics["auc_roc_macro"]], ["CV F1 macro", metrics["cv_best_score_f1_macro"]]]
    for cls in classes:
        rows.append([f"F1 {cls}", metrics["f1_per_class"][cls]])
        rows.append([f"Precision {cls}", metrics["precision_per_class"][cls]])
        rows.append([f"Recall {cls}", metrics["recall_per_class"][cls]])
    print(tabulate(rows, headers=["metric", "value"], tablefmt="github", floatfmt=".4f"))
    print(f"Saved {MODEL_DIR / 'readmission_classifier.pkl'}")
    print(f"Saved {PROCESSED / 'classifier_metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
