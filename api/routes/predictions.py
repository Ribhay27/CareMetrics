from __future__ import annotations

import numpy as np
import pandas as pd
import shap
import joblib
from fastapi import APIRouter, HTTPException

from api.models import HospitalScoreRequest, HospitalScoreResponse
from common.config import PROJECT_ROOT

router = APIRouter()


def _load_bundle(name: str):
    path = PROJECT_ROOT / "ml" / "models" / name
    if not path.exists():
        raise HTTPException(status_code=503, detail=f"Model file missing: {path}")
    return joblib.load(path)


@router.post("/score", response_model=HospitalScoreResponse)
def score_hospital(req: HospitalScoreRequest):
    classifier = _load_bundle("readmission_classifier.pkl")
    regressor = _load_bundle("quality_regressor.pkl")
    data = req.model_dump()
    clf_cols = classifier["feature_columns"]
    reg_cols = regressor["feature_columns"]
    all_cols = sorted(set(clf_cols) | set(reg_cols))
    X = pd.DataFrame([{c: data.get(c, 0.0) for c in all_cols}])
    clf_pred = classifier["model"].predict(X[clf_cols])[0]
    risk = classifier["label_encoder"].inverse_transform([clf_pred])[0]
    quality = float(regressor["model"].predict(X[reg_cols])[0])
    explainer = shap.TreeExplainer(classifier["model"])
    values = explainer.shap_values(X[clf_cols])
    arr = np.array(values)
    if arr.ndim == 3:
        arr = arr[:, :, int(clf_pred)][0]
    elif isinstance(values, list):
        arr = values[int(clf_pred)][0]
    else:
        arr = arr[0]
    top_idx = np.argsort(np.abs(arr))[::-1][:5]
    drivers = [{"feature": clf_cols[i], "contribution": float(arr[i])} for i in top_idx]
    return HospitalScoreResponse(predicted_risk_label=str(risk), predicted_quality_score=quality, top_shap_drivers=drivers)
