"""
train_lightgbm.py

Single-file training script for LightGBM classifier for EyeCare risk prediction.

Usage:
    python train_lightgbm.py /path/to/eyecare_dataset.csv

Outputs:
    - trained model saved to ./models/lightgbm_model.pkl
    - printed evaluation metrics and complexity metrics
    - CSV file with test predictions saved to ./models/test_predictions.csv

Sections are commented. Modify CSV_PATH or pass as CLI.
"""

# -------------------------
# Imports and requirements
# -------------------------
import os
import sys
import argparse
import warnings
from datetime import datetime
import pickle
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, RandomizedSearchCV
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    hamming_loss,
    classification_report,
    confusion_matrix,
)
import lightgbm as lgb

# Optional balancing
try:
    from imblearn.over_sampling import SMOTE
    IMBL_AVAILABLE = True
except Exception:
    IMBL_AVAILABLE = False

warnings.simplefilter("ignore")
np.random.seed(42)

# -------------------------
# Config / Defaults
# -------------------------
DEFAULT_MODEL_DIR = "models"
os.makedirs(DEFAULT_MODEL_DIR, exist_ok=True)

# If you prefer to hardcode path, set CSV_PATH below or pass it via CLI
CSV_PATH = "ml_models/dataset/New_data.csv"

# -------------------------
# Utility functions
# -------------------------
def safe_read_csv(path):
    df = pd.read_csv(path)
    print(f"Loaded dataset: {path} -> {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def basic_preprocess(df, target_col="Diagnosis"):
    """
    - Drops fully empty columns
    - Fills numeric NaNs with median
    - Fills categorical NaNs with "unknown"
    - Encodes categorical columns using LabelEncoder (returns encoders dict)
    """
    df = df.copy()
    # drop completely empty columns
    empty_cols = [c for c in df.columns if df[c].isna().all()]
    if empty_cols:
        print("Dropping empty columns:", empty_cols)
        df.drop(columns=empty_cols, inplace=True)

    # target must exist
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataframe columns: {df.columns.tolist()}")

    # identify numeric vs categorical
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in numeric_cols and c != target_col]

    # fill NaNs
    for c in numeric_cols:
        med = df[c].median()
        df[c].fillna(med, inplace=True)
    for c in cat_cols:
        df[c].fillna("unknown", inplace=True)

    # If target is numeric-like but actually categorical, convert to string
    df[target_col] = df[target_col].astype(str)

    encoders = {}
    # encode categorical and binary-ish columns
    for c in cat_cols + [target_col]:
        le = LabelEncoder()
        df[c] = le.fit_transform(df[c].astype(str))
        encoders[c] = le

    # return features X and labels y
    X = df.drop(columns=[target_col])
    y = df[target_col]
    return X, y, encoders, numeric_cols, cat_cols

def get_lgb_complexity_metrics(booster):
    """
    Extracts tree depth, node counts, tree count and feature count from trained booster.
    booster: lightgbm.Booster
    Returns: dict with metrics
    """
    dump = booster.dump_model()
    tree_info = dump.get("tree_info", [])
    n_trees = len(tree_info)
    depths = []
    node_counts = []
    for t in tree_info:
        # each tree has "tree_structure"
        def traverse(node):
            # node is dict; if 'left_child' in node => internal node
            if "left_child" in node and "right_child" in node:
                left = traverse(node["left_child"])
                right = traverse(node["right_child"])
                # depth is 1 + max child depth
                return 1 + max(left, right)
            else:
                return 1  # leaf node count depth 1

        depth = traverse(t["tree_structure"])
        depths.append(depth)

        # count nodes in tree by BFS
        def count_nodes(node):
            count = 1
            if "left_child" in node and "right_child" in node:
                count += count_nodes(node["left_child"])
                count += count_nodes(node["right_child"])
            return count

        node_counts.append(count_nodes(t["tree_structure"]))

    max_depth = int(np.max(depths)) if depths else 0
    avg_depth = float(np.mean(depths)) if depths else 0.0
    total_nodes = int(np.sum(node_counts))
    avg_nodes_per_tree = float(np.mean(node_counts)) if node_counts else 0.0
    feature_count = int(dump.get("max_feature_idx", -1) + 1) if "max_feature_idx" in dump else booster.num_feature()

    return {
        "n_trees": n_trees,
        "max_depth": max_depth,
        "avg_depth": round(avg_depth, 2),
        "total_nodes": total_nodes,
        "avg_nodes_per_tree": round(avg_nodes_per_tree, 2),
        "feature_count": feature_count,
    }

# -------------------------
# Model training pipeline
# -------------------------
def train_and_evaluate(
    csv_path,
    target_col="Diagnosis",
    test_size=0.2,
    val_size=0.1,
    use_smote=False,
    random_state=42,
    do_random_search=True,
    n_iter_search=25,
):
    df = safe_read_csv(csv_path)

    # Basic preprocess
    X, y, encoders, numeric_cols, cat_cols = basic_preprocess(df, target_col=target_col)
    feature_names = X.columns.tolist()
    print(f"Features: {len(feature_names)} -> {feature_names}")

    # Split
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        X, y, stratify=y, test_size=test_size, random_state=random_state
    )

    # Further split train-> train/val for early stopping if not using cv
    if val_size > 0:
        val_fraction_of_train = val_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train_full, y_train_full, stratify=y_train_full, test_size=val_fraction_of_train, random_state=random_state
        )
    else:
        X_train, y_train = X_train_full, y_train_full
        X_val, y_val = X_test, y_test

    print(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")

    # Optional class balancing (SMOTE) - only numeric features recommended
    if use_smote and IMBL_AVAILABLE:
        print("Applying SMOTE to training set (only numeric features used).")
        sm = SMOTE(random_state=random_state, n_jobs=1)
        X_train_np = X_train.values
        X_train_resampled, y_train_resampled = sm.fit_resample(X_train_np, y_train)
        X_train = pd.DataFrame(X_train_resampled, columns=feature_names)
        y_train = pd.Series(y_train_resampled)
        print("After SMOTE train shape:", X_train.shape)
    elif use_smote and not IMBL_AVAILABLE:
        print("SMOTE requested but imblearn not installed. Skipping SMOTE. Install imbalanced-learn to enable.")

    # Default params
    params = {
        "objective": "multiclass",
        "num_class": len(np.unique(y)),
        "metric": "multi_logloss",
        "verbosity": -1,
        "boosting_type": "gbdt",
        "seed": random_state,
        "learning_rate": 0.05,
        "num_leaves": 31,
        "max_depth": -1,
        "feature_pre_filter": False,
    }

    # Randomized search space
    param_dist = {
        "num_leaves": [16, 24, 31, 40, 64],
        "learning_rate": [0.01, 0.02, 0.05, 0.08, 0.1],
        "min_data_in_leaf": [10, 20, 30, 50, 100],
        "feature_fraction": [0.6, 0.7, 0.8, 0.9, 1.0],
        "bagging_fraction": [0.6, 0.7, 0.8, 0.9, 1.0],
        "bagging_freq": [0, 1, 3, 5],
        "max_depth": [-1, 6, 8, 12, 16],
    }

    best_params = params.copy()
    if do_random_search:
        print("Running quick RandomizedSearchCV (n_iter=%d) to tune key hyperparams..." % n_iter_search)
        # build lgb estimator wrapper for sklearn
        clf = lgb.LGBMClassifier(**params, n_estimators=500, n_jobs=-1)
        fit_params = {
            "eval_set": [(X_val, y_val)],
            "eval_metric": "multi_logloss",
        }
        rs = RandomizedSearchCV(
            estimator=clf,
            param_distributions=param_dist,
            n_iter=n_iter_search,
            scoring="f1_weighted",
            cv=StratifiedKFold(n_splits=3, shuffle=True, random_state=random_state),
            verbose=1,
            random_state=random_state,
            n_jobs=-1,
        )
        rs.fit(X_train, y_train, **fit_params)
        print("RandomizedSearch best score:", rs.best_score_)
        best_params = rs.best_params_
        # ensure required params exist
        best_params.update({"objective": "multiclass", "num_class": len(np.unique(y)), "verbosity": -1, "seed": random_state})
        print("Best params selected:", best_params)
    else:
        print("Skipping random search, using default params.")

    # Train final model with early stopping using combined train+val if desired or train on train_full
    final_clf = lgb.LGBMClassifier(**best_params, n_estimators=1000, n_jobs=-1)
    final_clf.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="multi_logloss",
        callbacks=[lgb.early_stopping(stopping_rounds=50)],
    )

    # Predictions
    y_pred_test = final_clf.predict(X_test)
    y_pred_proba = final_clf.predict_proba(X_test) if hasattr(final_clf, "predict_proba") else None

    # Metrics
    acc = accuracy_score(y_test, y_pred_test)
    f1_w = f1_score(y_test, y_pred_test, average="weighted")
    f1_macro = f1_score(y_test, y_pred_test, average="macro")
    ham_loss = hamming_loss(y_test, y_pred_test)  # for single-label this equals fraction incorrect labels
    # subset accuracy (same as accuracy_score for single-label)
    subset_acc = accuracy_score(y_test, y_pred_test)

    print("\n=== EVALUATION METRICS ===")
    print(f"Accuracy: {acc:.4f}")
    print(f"F1 (weighted): {f1_w:.4f}")
    print(f"F1 (macro): {f1_macro:.4f}")
    print(f"Hamming loss: {ham_loss:.4f}")
    print(f"Subset accuracy: {subset_acc:.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, y_pred_test, digits=4))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred_test))

    # Save model
    model_path = os.path.join(DEFAULT_MODEL_DIR, "lightgbm_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump({"model": final_clf, "encoders": encoders, "feature_names": feature_names}, f)
    print(f"\nModel saved to: {model_path}")

    return {
        "accuracy": acc,
        "f1_weighted": f1_w,
        "f1_macro": f1_macro,
        "hamming_loss": ham_loss,
        "subset_accuracy": subset_acc,
        "model_path": model_path,
    }

# -------------------------
# CLI Entrypoint
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Train LightGBM on EyeCare dataset CSV.")
    parser.add_argument("csv", nargs="?", default=CSV_PATH, help="Path to eyecare CSV dataset")
    parser.add_argument("--target", default="Diagnosis", help="Target column name")
    parser.add_argument("--smote", action="store_true", help="Apply SMOTE balancing to training set (requires imblearn)")
    parser.add_argument("--no-random-search", dest="do_rs", action="store_false", help="Disable randomized hyperparam search")
    parser.add_argument("--n-iter", type=int, default=25, help="Random search iterations")
    args = parser.parse_args()

    if not args.csv:
        print(f"Error: CSV path not provided. Usage: python train_lightgbm.py /path/to/eyecare_dataset.csv\n"
              f"Default path: {CSV_PATH}")
        sys.exit(1)
    if not os.path.exists(args.csv):
        print("Error: CSV file not found:", args.csv)
        sys.exit(1)

    out = train_and_evaluate(
        csv_path=args.csv,
        target_col=args.target,
        use_smote=args.smote,
        do_random_search=args.do_rs,
        n_iter_search=args.n_iter,
    )

    print("\nFinished. Summary:")
    print(out)

if __name__ == "__main__":
    main()
