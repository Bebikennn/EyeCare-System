from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import joblib
import pandas as pd

from rules_engine import infer_probable_condition


MODEL_PATH = Path(__file__).resolve().parent / "risk_model.joblib"
DATASET_PATH = Path(__file__).resolve().parent / "dataset" / "EyeConditions_CLEAN_RISK.csv"


def predict_user(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Predict overall risk, then (if HIGH) infer one probable condition via rules."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found: {MODEL_PATH}. Run train_risk_model.py first."
        )

    pipeline = joblib.load(MODEL_PATH)

    expected = getattr(pipeline, "feature_names_in_", None)
    if expected is None:
        raise ValueError("Loaded pipeline does not expose feature_names_in_. Retrain the model.")

    row = {col: input_dict.get(col, None) for col in list(expected)}
    X = pd.DataFrame([row])
    risk_probability = float(pipeline.predict_proba(X)[:, 1][0])
    risk_label = "HIGH" if risk_probability >= 0.5 else "LOW"

    if risk_label == "LOW":
        return {
            "risk_probability": risk_probability,
            "risk_label": risk_label,
            "probable_condition": "N/A",
            "triggered_rules": [],
            "note": "Probable condition only. Not a medical diagnosis.",
        }

    rule_result = infer_probable_condition(input_dict)

    return {
        "risk_probability": risk_probability,
        "risk_label": risk_label,
        "probable_condition": rule_result.probable_condition,
        "triggered_rules": rule_result.triggered_rules,
        "confidence_level": rule_result.confidence_level,
        "note": "Probable condition only. Not a medical diagnosis.",
    }


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)
    feature_cols = [c for c in df.columns if c != "Eye_Disease_Risk"]

    # Sample input dict built from actual dataset columns
    sample_row = df.loc[0, feature_cols].to_dict()

    output = predict_user(sample_row)
    print("Sample input (from dataset row 0):")
    print({k: sample_row[k] for k in list(sample_row)[:10]})
    print("...")
    print("\nPrediction output:")
    print(output)


if __name__ == "__main__":
    main()
