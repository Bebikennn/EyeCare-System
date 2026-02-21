"""ML Prediction Service (Two-stage: LightGBM risk + rules).

Stage 1 (ML): overall risk (Eye_Disease_Risk) via a saved sklearn Pipeline.
Stage 2 (Rules): probable condition (one-of-7) only when risk is HIGH.

This replaces the older direct-disease predictor that could leak symptom-derived features.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd

from ml_models.rules_engine import CONDITIONS, infer_probable_condition, score_conditions


MODEL_PATH = Path(__file__).parent.parent / "ml_models" / "risk_model.joblib"
_pipeline_cache = None
_pipeline_lock = threading.Lock()

def load_model():
    """
    Load the trained risk pipeline with thread-safe caching.
    Model is loaded once and cached in memory for better performance.
    """
    global _pipeline_cache

    if _pipeline_cache is not None:
        return _pipeline_cache

    with _pipeline_lock:
        if _pipeline_cache is not None:
            return _pipeline_cache

        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Risk model not found at {MODEL_PATH}. Run ml_models/train_risk_model.py first."
            )

        print(f"📦 Loading risk model pipeline from {MODEL_PATH}...")
        _pipeline_cache = joblib.load(MODEL_PATH)
        print("✅ Risk model pipeline loaded and cached")
        return _pipeline_cache

def preload_model():
    """Preload model at startup to avoid first-request latency"""
    try:
        load_model()
        print("🚀 ML model preloaded successfully")
    except Exception as e:
        print(f"⚠️  Failed to preload ML model: {e}")

def predict_risk(assessment_data):
    """Predict overall eye-disease risk, then infer one probable condition if HIGH.

    Returns a dict compatible with the existing assessment flow, plus new fields:
    - risk_probability, risk_label (HIGH/LOW)
    - probable_condition, triggered_rules, confidence_level
    """
    try:
        pipeline = load_model()
        X = _build_feature_frame(pipeline, assessment_data)

        risk_probability = float(pipeline.predict_proba(X)[:, 1][0])
        risk_label = "HIGH" if risk_probability >= 0.5 else "LOW"

        if risk_label == "LOW":
            probable_condition = "N/A"
            triggered_rules: List[str] = []
            confidence_level = "LOW"
            per_condition = {}
            condition_risk_flag = "N/A"
        else:
            rr = infer_probable_condition(assessment_data)
            probable_condition = rr.probable_condition
            triggered_rules = rr.triggered_rules
            confidence_level = rr.confidence_level
            condition_risk_flag = _condition_risk_flag(probable_condition)

            # Build per-condition probabilities for UI.
            # - The top probable condition uses the ML risk_probability as its confidence.
            # - The remaining probability mass is distributed ONLY across conditions
            #   that are supported by user inputs (rule score > 0).
            #
            # Note: this is still a heuristic distribution (rules + overall risk), not a
            # calibrated multi-class disease probability model.
            predicted_p = max(0.0, min(1.0, float(risk_probability)))
            remainder = max(0.0, 1.0 - predicted_p)

            scores = score_conditions(assessment_data)
            other_candidates = [
                c
                for c in CONDITIONS
                if c != probable_condition
                and c in scores
                and scores[c].score > 0
            ]
            other_score_sum = sum(scores[c].score for c in other_candidates)

            per_condition = {c: 0.0 for c in CONDITIONS}
            if probable_condition in per_condition:
                per_condition[probable_condition] = predicted_p

            if remainder > 0 and other_score_sum > 0:
                for c in other_candidates:
                    per_condition[c] = remainder * (scores[c].score / other_score_sum)
            elif remainder > 0:
                # No evidence-backed alternative conditions; keep remainder explicit.
                per_condition["Other / Unspecified"] = remainder

        # Keep existing keys used throughout the backend.
        # risk_score is made consistent with the ML probability (0-100).
        risk_score = round(risk_probability * 100.0, 2)
        risk_level = "High" if risk_label == "HIGH" else "Low"

        return {
            # New fields
            "risk_probability": risk_probability,
            "risk_label": risk_label,
            "probable_condition": probable_condition,
            "triggered_rules": triggered_rules,
            "confidence_level": confidence_level,
            "condition_risk_flag": condition_risk_flag,
            "note": "Probable condition only. Not a medical diagnosis.",

            # Legacy/compat fields
            "predicted_disease": probable_condition,
            "confidence": risk_probability,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "per_disease_probabilities": per_condition,
        }
    except Exception as e:
        raise Exception(f"Prediction error: {str(e)}")


def _condition_risk_flag(probable_condition: str) -> str:
    """Map probable condition to a user-facing severity flag.

    This is a product rule provided by the project, not learned from the dataset.
    """
    if not probable_condition:
        return "Unknown"

    # Special cases produced by the rules engine
    if probable_condition == "N/A":
        return "N/A"
    if probable_condition == "Unspecified High Risk":
        return "High Risk"

    high = {"Myopia", "Dry Eye", "Presbyopia"}
    moderate = {"Astigmatism", "Hyperopia"}
    low = {"Blurred Vision", "Light Sensitivity"}

    if probable_condition in high:
        return "High Risk"
    if probable_condition in moderate:
        return "Moderate Risk"
    if probable_condition in low:
        return "Low Risk"
    return "Unknown"


def _build_feature_frame(pipeline: Any, assessment_data: Dict[str, Any]) -> pd.DataFrame:
    """Create a single-row DataFrame aligned to the exact feature columns used at training time.

    - Missing expected columns are filled with NaN (imputers handle them).
    - Extra provided keys are ignored.
    """
    expected = getattr(pipeline, "feature_names_in_", None)
    if expected is None:
        # Fallback: if sklearn didn't store feature names for some reason.
        raise ValueError("Loaded pipeline does not expose feature_names_in_. Retrain the model.")

    row = {col: assessment_data.get(col, None) for col in list(expected)}
    return pd.DataFrame([row])

def calculate_risk_score(data):
    """Deprecated: kept for backward compatibility.

    New system uses ML probability * 100 as the primary risk score.
    """
    try:
        return float(data.get("risk_score", 0))
    except Exception:
        return 0.0


def determine_risk_level(risk_score, disease, confidence):
    """Deprecated: kept for backward compatibility."""
    try:
        return "High" if float(risk_score) >= 50 else "Low"
    except Exception:
        return "Low"

def get_recommendations(risk_level, predicted_disease, assessment_data):
    """Generate recommendations."""
    recommendations = []
    if risk_level in ["High", "Critical"]:
        recommendations.append({"text": "Schedule urgent eye exam within 1-3 months", "priority": "High", "category": "Medical"})
    elif risk_level == "Moderate":
        recommendations.append({"text": "Schedule eye check-up within 3-6 months", "priority": "Medium", "category": "Medical"})
    else:
        recommendations.append({"text": "Maintain regular eye check-ups every 12 months", "priority": "Low", "category": "Prevention"})
    
    if float(assessment_data.get('Screen_Time_Hours', 0)) > 6:
        recommendations.append({"text": "Reduce screen time and follow 20-20-20 rule", "priority": "High", "category": "Lifestyle"})
    if float(assessment_data.get('Sleep_Hours', 7)) < 6:
        recommendations.append({"text": "Improve sleep to 7-9 hours per night", "priority": "High", "category": "Lifestyle"})
    if assessment_data.get('Smoker'):
        recommendations.append({"text": "Quit smoking to reduce eye disease risk", "priority": "High", "category": "Lifestyle"})
    if float(assessment_data.get('Water_Intake_Liters', 0)) < 2:
        recommendations.append({"text": "Increase water intake to 6-8 glasses daily", "priority": "Medium", "category": "Nutrition"})
    return recommendations

