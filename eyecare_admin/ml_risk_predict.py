"""Admin two-stage predictor.

Loads the Stage-1 risk model pipeline from `models/risk_model.joblib` and applies
Stage-2 rules only when Stage-1 risk is HIGH.

This module is designed to be imported by Flask routes.
"""

from __future__ import annotations

import os
import threading
from typing import Any, Mapping

import joblib
import pandas as pd

from ml_rules_engine import infer_probable_condition


_MODEL_PATH = os.path.join("models", "risk_model.joblib")
_model_lock = threading.Lock()
_cached_pipeline: Any | None = None


def load_risk_pipeline() -> Any:
    global _cached_pipeline
    if _cached_pipeline is not None:
        return _cached_pipeline

    with _model_lock:
        if _cached_pipeline is not None:
            return _cached_pipeline
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Risk model not found at {_MODEL_PATH}. Run train_risk_model.py first."
            )
        _cached_pipeline = joblib.load(_MODEL_PATH)
        return _cached_pipeline


def _normalize_features(input_data: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize incoming payload keys to the dataset column names."""

    # Accept both snake_case and exact dataset-style names.
    mapping = {
        "age": "Age",
        "gender": "Gender",
        "bmi": "BMI",
        "screen_time_hours": "Screen_Time_Hours",
        "sleep_hours": "Sleep_Hours",
        "smoker": "Smoker",
        "alcohol_use": "Alcohol_Use",
        "diabetes": "Diabetes",
        "hypertension": "Hypertension",
        "family_history_eye_disease": "Family_History_Eye_Disease",
        "outdoor_exposure_hours": "Outdoor_Exposure_Hours",
        "diet_score": "Diet_Score",
        "water_intake_liters": "Water_Intake_Liters",
        "glasses_usage": "Glasses_Usage",
        "previous_eye_surgery": "Previous_Eye_Surgery",
        "physical_activity_level": "Physical_Activity_Level",
    }

    out: dict[str, Any] = {}

    for k, v in input_data.items():
        if k in ("Eye_Disease_Risk", "eye_disease_risk"):
            continue

        # If the key already matches a dataset column, preserve it.
        if k in mapping.values():
            out[k] = v
            continue

        k_norm = str(k).strip().lower()
        if k_norm in mapping:
            out[mapping[k_norm]] = v

    # Normalize gender formatting if provided.
    g = out.get("Gender")
    if isinstance(g, str):
        g2 = g.strip().lower()
        if g2 in ("male", "m"):
            out["Gender"] = "Male"
        elif g2 in ("female", "f"):
            out["Gender"] = "Female"

    return out


def _condition_risk_flag(probable_condition: str) -> str:
    high = {"Myopia", "Dry Eye", "Presbyopia", "Unspecified High Risk"}
    moderate = {"Astigmatism", "Hyperopia"}
    low = {"Blurred Vision", "Light Sensitivity"}

    if probable_condition in high:
        return "High Risk"
    if probable_condition in moderate:
        return "Moderate Risk"
    if probable_condition in low:
        return "Low Risk"
    if probable_condition == "N/A":
        return "N/A"
    return "N/A"


def predict_risk_two_stage(input_data: Mapping[str, Any]) -> dict[str, Any]:
    pipeline = load_risk_pipeline()

    normalized = _normalize_features(input_data)

    # Align to model expected feature order.
    if not hasattr(pipeline, "feature_names_in_"):
        raise RuntimeError("Loaded pipeline is missing feature_names_in_. Re-train with sklearn.")

    feature_names = list(getattr(pipeline, "feature_names_in_"))

    row = {name: normalized.get(name, None) for name in feature_names}
    X = pd.DataFrame([row], columns=feature_names)

    proba = float(pipeline.predict_proba(X)[0][1])

    # Stage-1 risk label for rule triggering.
    risk_label = "HIGH" if proba >= 0.5 else "LOW"

    # Optional tri-level for admin display.
    if proba >= 0.66:
        risk_level = "High"
    elif proba >= 0.33:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    probable_condition = "N/A"
    triggered_rules: list[str] = []
    confidence_level = "N/A"

    if risk_label == "HIGH":
        rr = infer_probable_condition(normalized)
        probable_condition = rr.probable_condition
        triggered_rules = rr.triggered_rules
        confidence_level = rr.confidence_level

    condition_risk_flag = _condition_risk_flag(probable_condition)

    return {
        # New fields
        "risk_probability": proba,
        "risk_label": risk_label,
        "risk_level": risk_level,
        "probable_condition": probable_condition,
        "triggered_rules": triggered_rules,
        "confidence_level": confidence_level,
        "condition_risk_flag": condition_risk_flag,
        "note": "Two-stage system: ML predicts overall risk; condition inferred by rules only if risk is HIGH.",
        # Back-compat-ish fields used elsewhere in admin
        "risk_score": proba * 100.0,
        "predicted_disease": probable_condition,
        "confidence": max(proba, 1.0 - proba),
        "all_predictions": {
            "HIGH_RISK": proba,
            "LOW_RISK": 1.0 - proba,
        },
    }
