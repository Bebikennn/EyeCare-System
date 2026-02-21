import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from pathlib import Path
import pickle

# Paths
DATA_PATH = Path(__file__).parent / "dataset" / "EyeConditions.csv"
MODEL_PATH = Path(__file__).parent.parent / "models" / "lightgbm_model.pkl"

# If any rows with these diagnoses remain, drop them defensively
EXCLUDED_DIAGNOSES = {"Keratitis"}


def train_lightgbm_model(test_size: float = 0.2, random_state: int = 42):
    print("=" * 60)
    print("Training LightGBM model for EyeCare backend")
    print("=" * 60)

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    # Avoid Unicode emoji in console output (Windows cp1252 safe)
    print(f"\nLoading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    if "Diagnosis" not in df.columns:
        raise ValueError("Dataset must contain a 'Diagnosis' column as target")

    # Drop excluded diagnoses if present (defensive; your CSV should already have Keratitis removed)
    before = len(df)
    df = df[~df["Diagnosis"].astype(str).isin(EXCLUDED_DIAGNOSES)].copy()
    removed = before - len(df)
    if removed:
        print(f"🧹 Removed {removed} rows with excluded diagnoses: {sorted(EXCLUDED_DIAGNOSES)}")

    print(f"Dataset loaded: {len(df)} rows, {len(df.columns) - 1} features + target")
    print("Sample diagnoses:", sorted(df["Diagnosis"].unique()))

    # Target
    y = df["Diagnosis"].astype(str)

    # Features: everything except Diagnosis (keep 'Risk Score' as a feature)
    X = df.drop(columns=["Diagnosis"])

    encoders = {}

    # Encode Gender as 0/1 using LabelEncoder so it matches ml_predict.py
    if "Gender" in X.columns:
        le_gender = LabelEncoder()
        X["Gender"] = le_gender.fit_transform(X["Gender"].astype(str))
        encoders["Gender"] = le_gender
        print("Encoded 'Gender' with LabelEncoder -> stored in encoders['Gender']")

    # Encode Diagnosis labels
    le_diag = LabelEncoder()
    y_encoded = le_diag.fit_transform(y)
    encoders["Diagnosis"] = le_diag
    print("Encoded 'Diagnosis' with LabelEncoder -> stored in encoders['Diagnosis']")
    print("Classes:", list(le_diag.classes_))

    # Train / test split
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y_encoded,
        test_size=test_size,
        random_state=random_state,
        stratify=y_encoded,
    )

    print("\nData split:")
    print("  X_train:", X_train.shape)
    print("  X_test :", X_test.shape)

    # LightGBM model (tuned for good accuracy on this small tabular dataset)
    num_classes = len(le_diag.classes_)
    model = lgb.LGBMClassifier(
        objective="multiclass",
        num_class=num_classes,
        learning_rate=0.05,
        n_estimators=500,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=random_state,
        n_jobs=-1,
    )

    print("\nTraining LightGBM model...")
    model.fit(X_train, y_train)
    print("Model trained")

    # Evaluation
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)")

    print("\nClassification report:")
    print(classification_report(y_test, y_pred, target_names=le_diag.classes_))

    # Save model in the exact format used by services/ml_predict.py
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(
            {
                "model": model,
                "encoders": encoders,
                "feature_names": list(X.columns),
            },
            f,
        )

    print(f"\nSaved model to: {MODEL_PATH}")
    print("Feature order:", list(X.columns))

    return {
        "accuracy": float(accuracy),
        "model_path": str(MODEL_PATH),
        "n_classes": int(num_classes),
        "classes": list(le_diag.classes_),
    }


if __name__ == "__main__":
    result = train_lightgbm_model()
    print("\nTraining summary:", result)
