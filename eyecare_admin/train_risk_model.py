"""Train the two-stage Stage-1 risk model for the admin site.

Stage 1: LightGBM binary classifier predicting overall Eye_Disease_Risk.
Stage 2: Rules engine (see ml_rules_engine.py) is applied only when Stage 1 is HIGH.

This script trains and saves a single sklearn Pipeline to `models/risk_model.joblib`.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

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


DATASET_PATH_DEFAULT = os.path.join("models", "dataset", "EyeConditions_CLEAN_RISK.csv")
MODEL_PATH_DEFAULT = os.path.join("models", "risk_model.joblib")


def resolve_dataset_path(dataset_path: str | None = None) -> str:
    """Resolve dataset path from common admin upload/storage locations.

    Accepts:
    - absolute path
    - relative path
    - bare filename (e.g., EyeConditions_CLEAN_RISK.csv)
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    requested = (dataset_path or DATASET_PATH_DEFAULT).strip()

    candidates: list[str] = []

    if os.path.isabs(requested):
        candidates.append(requested)
    else:
        candidates.extend(
            [
                requested,
                os.path.join(base_dir, requested),
                os.path.join(base_dir, "ml", "datasets", requested),
                os.path.join(base_dir, "models", "dataset", requested),
            ]
        )

    # Also attempt basename in known folders (covers values like `ml/datasets/file.csv`).
    file_name = os.path.basename(requested)
    candidates.extend(
        [
            os.path.join(base_dir, "ml", "datasets", file_name),
            os.path.join(base_dir, "models", "dataset", file_name),
        ]
    )

    # De-duplicate while preserving order.
    seen = set()
    unique_candidates = []
    for path in candidates:
        if path not in seen:
            seen.add(path)
            unique_candidates.append(path)

    for path in unique_candidates:
        if os.path.exists(path):
            return path

    raise FileNotFoundError(
        f"Dataset not found: {requested}. Tried: {unique_candidates}"
    )


@dataclass
class TrainResult:
    model_path: str
    dataset_path: str
    n_rows: int
    n_features_raw: int
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: list[list[int]]


def _build_pipeline(numeric_features: list[str], categorical_features: list[str]) -> Pipeline:
    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop",
    )

    # Keep trees relatively constrained to reduce memorization.
    model = LGBMClassifier(
        random_state=42,
        n_estimators=300,
        learning_rate=0.05,
        num_leaves=24,
        max_depth=5,
        min_data_in_leaf=30,
        subsample=0.8,
        colsample_bytree=0.8,
    )

    pipe = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])

    # Helpful for feature importance extraction.
    try:
        preprocessor.set_output(transform="pandas")
    except Exception:
        pass

    return pipe


def train_risk_model(
    dataset_path: str = DATASET_PATH_DEFAULT,
    model_path: str = MODEL_PATH_DEFAULT,
    save_metrics_to_db: bool = True,
) -> TrainResult:
    dataset_path = resolve_dataset_path(dataset_path)

    df = pd.read_csv(dataset_path)

    if "Eye_Disease_Risk" not in df.columns:
        raise ValueError("Expected target column 'Eye_Disease_Risk' not found in dataset")

    y = df["Eye_Disease_Risk"].astype(int)
    X = df.drop(columns=["Eye_Disease_Risk"]).copy()

    # Treat Gender as categorical; everything else numeric.
    categorical_features = [c for c in X.columns if c.lower() == "gender"]
    numeric_features = [c for c in X.columns if c not in categorical_features]

    pipe = _build_pipeline(numeric_features=numeric_features, categorical_features=categorical_features)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=y,
    )

    pipe.fit(X_train, y_train)

    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    try:
        auc = float(roc_auc_score(y_test, y_proba))
    except Exception:
        auc = float("nan")

    cm = confusion_matrix(y_test, y_pred).tolist()

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(pipe, model_path)

    result = TrainResult(
        model_path=model_path,
        dataset_path=dataset_path,
        n_rows=int(len(df)),
        n_features_raw=int(X.shape[1]),
        accuracy=acc,
        precision=prec,
        recall=rec,
        f1=f1,
        roc_auc=auc,
        confusion_matrix=cm,
    )

    if save_metrics_to_db:
        _save_metrics_to_db(result=result, pipeline=pipe)

    return result


def _save_metrics_to_db(*, result: TrainResult, pipeline: Pipeline) -> None:
    # Avoid requiring DB for local training runs.
    try:
        from app import app
        from database import db, MLMetrics

        with app.app_context():
            model_version = f"RiskModel-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            feature_importance_json = _extract_feature_importance_json(pipeline)

            metrics = MLMetrics(
                model_version=model_version,
                accuracy=result.accuracy,
                precision=result.precision,
                recall=result.recall,
                f1_score=result.f1,
                confusion_matrix=json.dumps(result.confusion_matrix),
                feature_importance=feature_importance_json,
                dataset_size=result.n_rows,
            )

            db.session.add(metrics)
            db.session.commit()
    except Exception:
        # Best-effort only.
        return


def _extract_feature_importance_json(pipeline: Pipeline) -> str:
    try:
        model = pipeline.named_steps["model"]
        pre = pipeline.named_steps["preprocessor"]

        importances = getattr(model, "feature_importances_", None)
        if importances is None:
            return json.dumps({})

        # Prefer names from pandas output if available.
        feature_names: list[str]
        try:
            feature_names = list(pre.get_feature_names_out())
        except Exception:
            feature_names = [f"f{i}" for i in range(len(importances))]

        pairs = list(zip(feature_names, importances, strict=False))
        pairs.sort(key=lambda t: float(t[1]), reverse=True)

        # Store all; UI can slice top-N.
        return json.dumps({name: float(val) for name, val in pairs})
    except Exception:
        return json.dumps({})


def main() -> None:
    print("=" * 70)
    print("Admin Risk Model Training (Stage 1: Eye_Disease_Risk)")
    print("=" * 70)

    res = train_risk_model()

    print("\nSaved:")
    print(f"  - Model: {res.model_path}")
    print("\nMetrics:")
    print(f"  - rows: {res.n_rows}")
    print(f"  - features(raw): {res.n_features_raw}")
    print(f"  - accuracy: {res.accuracy:.4f}")
    print(f"  - precision: {res.precision:.4f}")
    print(f"  - recall: {res.recall:.4f}")
    print(f"  - f1: {res.f1:.4f}")
    if not np.isnan(res.roc_auc):
        print(f"  - roc_auc: {res.roc_auc:.4f}")
    print(f"  - confusion_matrix: {res.confusion_matrix}")


if __name__ == "__main__":
    main()
