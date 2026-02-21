"""README

This project implements a two-stage EyeCare prediction system:

- Stage 1 (ML): predicts overall eye-disease risk (binary) using LightGBM.
- Stage 2 (Rules): infers one probable condition (one-of-7) only when Stage 1 risk is HIGH.

Important: We do NOT train ML to predict the 7 eye conditions directly when a dataset contains
symptom-derived features (e.g., symptom scores), because that creates label leakage and unrealistically
high accuracy. Instead, ML is used only for overall risk, and condition selection is handled by a
rule-based engine that uses pre-condition factors.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATASET_PATH = Path(__file__).resolve().parent / "dataset" / "EyeConditions_CLEAN_RISK.csv"
MODEL_PATH = Path(__file__).resolve().parent / "risk_model.joblib"


def _build_pipeline(X: pd.DataFrame) -> Pipeline:
    numeric_features = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_features = [c for c in X.columns if c not in numeric_features]

    numeric_transformer = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median"))]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    # Keep feature names consistent into LightGBM to avoid sklearn warnings.
    preprocessor.set_output(transform="pandas")

    # Constrained-ish params to reduce memorization.
    # (LightGBM will still be strong; these keep the trees shallow and leaves limited.)
    model = LGBMClassifier(
        n_estimators=400,
        learning_rate=0.05,
        num_leaves=24,  # 16–32
        max_depth=5,  # 4–6
        min_data_in_leaf=30,  # >= 30
        feature_fraction=0.8,
        bagging_fraction=0.8,
        bagging_freq=1,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])


def main() -> None:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    df = pd.read_csv(DATASET_PATH)

    target_col = "Eye_Disease_Risk"
    if target_col not in df.columns:
        raise ValueError(
            f"Target column '{target_col}' not found. Available columns: {list(df.columns)}"
        )

    y = df[target_col]
    X = df.drop(columns=[target_col])

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y,
    )

    pipeline = _build_pipeline(X_train)
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    # roc_auc requires both classes present
    roc_auc = (
        roc_auc_score(y_test, y_proba)
        if len(np.unique(y_test)) == 2
        else float("nan")
    )

    cm = confusion_matrix(y_test, y_pred)

    print("Stage 1 (Risk) Evaluation")
    print(f"Accuracy : {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall   : {rec:.4f}")
    print(f"F1       : {f1:.4f}")
    print(f"ROC AUC  : {roc_auc:.4f}")
    print("Confusion Matrix:")
    print(cm)

    joblib.dump(pipeline, MODEL_PATH)
    print(f"\nSaved model pipeline to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
