import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import json
from datetime import datetime
import os
import sys

# Add the eyecare_admin directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EXCLUDED_DIAGNOSES = {
    # Removed diseases / labels (keep defensive filtering even if dataset is already cleaned)
    'Cataract',
    'Allergic Conjunctivitis',
    'Eye Strain / CVS',
    'Digital Eye Strain',
    'Eye Strain',
    'Eye Strain CSV',
}

def train_lightgbm_model():
    """Train LightGBM model on eyecare dataset"""
    
    print("=" * 60)
    print("LightGBM Model Training")
    print("=" * 60)
    
    # Load dataset (updated to use EyeConditions.csv for admin site)
    dataset_path = 'models/dataset/EyeConditions.csv'
    print(f"\nLoading dataset from: {dataset_path}")
    df = pd.read_csv(dataset_path)
    # Remove excluded diseases if present
    if 'Diagnosis' in df.columns:
        before = len(df)
        df = df[~df['Diagnosis'].astype(str).isin(EXCLUDED_DIAGNOSES)].copy()
        removed = before - len(df)
        if removed:
            print(f"\nRemoved {removed} rows with excluded diagnoses: {sorted(EXCLUDED_DIAGNOSES)}")
    
    print(f"DataFrame loaded successfully")
    print(f"  - Total records: {len(df)}")
    print(f"  - Total features: {len(df.columns) - 1}")
    print("\nFirst 5 rows:")
    print(df.head())
    
    # Define the target variable 'y' as the 'Diagnosis' column
    y = df['Diagnosis']
    
    # Instantiate LabelEncoder and fit-transform the 'y' variable
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(y)
    
    print("\nTarget variable 'y' encoded successfully")
    print(f"  - Classes: {list(label_encoder.classes_)}")
    print(f"  - Number of classes: {len(label_encoder.classes_)}")
    
    # Create the feature DataFrame 'X' by dropping the 'Diagnosis' column
    X = df.drop('Diagnosis', axis=1)
    
    # Convert the 'Gender' column in X into numerical format using one-hot encoding
    X = pd.get_dummies(X, columns=['Gender'], drop_first=True)
    
    print("\nFeatures 'X' prepared and 'Gender' column one-hot encoded")
    print(f"  - Feature columns: {list(X.columns)}")
    
    # Split the preprocessed X and y into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("\nData split into training and testing sets successfully")
    print(f"  - X_train shape: {X_train.shape}")
    print(f"  - X_test shape: {X_test.shape}")
    print(f"  - y_train shape: {y_train.shape}")
    print(f"  - y_test shape: {y_test.shape}")
    
    # Instantiate the LGBMClassifier with a random state for reproducibility
    print("\nTraining LightGBM model...")
    lgbm_model = lgb.LGBMClassifier(random_state=42)
    
    # Fit the model to the training data
    lgbm_model.fit(X_train, y_train)
    
    print("LightGBM model trained successfully")
    
    # Make predictions on the test set
    y_pred = lgbm_model.predict(X_test)
    
    # Calculate the accuracy score
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nModel Performance:")
    print(f"  - Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    # Additional metrics
    print("\nClassification Report:")
    class_report = classification_report(y_test, y_pred, target_names=label_encoder.classes_, output_dict=True)
    print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
    
    print("\nConfusion Matrix:")
    conf_matrix = confusion_matrix(y_test, y_pred)
    print(conf_matrix)
    
    # Calculate weighted averages
    precision_weighted = class_report['weighted avg']['precision']
    recall_weighted = class_report['weighted avg']['recall']
    f1_weighted = class_report['weighted avg']['f1-score']
    
    # Extract feature importances
    feature_importances = lgbm_model.feature_importances_
    
    # Create a pandas Series from these importances, using X_train column names as the index
    feature_names = X_train.columns
    feature_importance_series = pd.Series(feature_importances, index=feature_names)
    
    # Sort the feature importances in descending order
    sorted_feature_importance = feature_importance_series.sort_values(ascending=False)
    
    print("\nFeature Importances (Top 10):")
    for idx, (feature, importance) in enumerate(sorted_feature_importance.head(10).items(), 1):
        print(f"  {idx:2d}. {feature:30s}: {importance:8.2f} ({importance/feature_importances.sum()*100:.2f}%)")
    
    # Save feature importance plot (optional)
    plot_path = None
    try:
        import matplotlib.pyplot as plt

        print("\nCreating feature importance visualization...")
        plt.figure(figsize=(10, 8))
        sorted_feature_importance.plot(kind='barh')
        plt.title('LightGBM Feature Importances')
        plt.xlabel('Feature Importance')
        plt.ylabel('Features')
        plt.gca().invert_yaxis()
        plt.tight_layout()

        plot_path = 'models/feature_importance_plot.png'
        os.makedirs(os.path.dirname(plot_path), exist_ok=True)
        plt.savefig(plot_path)
        print(f"Plot saved to: {plot_path}")
        plt.close()
    except ModuleNotFoundError:
        print("Skipping feature importance plot (matplotlib not installed)")
    
    # Save the model
    model_path = 'models/eyecare_lightgbm_model.pkl'
    print(f"\nSaving model to: {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': lgbm_model,
            'label_encoder': label_encoder,
            'feature_names': list(X.columns)
        }, f)
    print("Model saved successfully")
    
    # Save metrics to database (optional)
    print("\nSaving metrics to database...")
    model_version = f'LightGBM-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    try:
        from app import app  # lazy import to avoid requiring DB for local training runs
        from database import db, MLMetrics

        with app.app_context():
            # Prepare feature importance as JSON
            feature_importance_dict = {}
            for feature, importance in sorted_feature_importance.items():
                feature_importance_dict[feature] = float(importance)

            # Prepare detailed classification report
            class_report_formatted = {
                'classes': {},
                'weighted_avg': {
                    'precision': precision_weighted,
                    'recall': recall_weighted,
                    'f1-score': f1_weighted
                },
                'accuracy': accuracy
            }

            for class_name in label_encoder.classes_:
                if class_name in class_report:
                    class_report_formatted['classes'][class_name] = {
                        'precision': class_report[class_name]['precision'],
                        'recall': class_report[class_name]['recall'],
                        'f1-score': class_report[class_name]['f1-score'],
                        'support': class_report[class_name]['support']
                    }

            # Create notes with additional info
            notes = {
                'algorithm': 'LightGBM Classifier',
                'n_classes': len(label_encoder.classes_),
                'classes': list(label_encoder.classes_),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'n_features': X_train.shape[1],
                'feature_names': list(X.columns),
                'classification_report': class_report_formatted,
                'random_state': 42
            }

            # Create ML metrics record (only include optional fields if supported by schema)
            metrics_kwargs = {
                'model_version': model_version,
                'accuracy': float(accuracy),
                'precision': float(precision_weighted),
                'recall': float(recall_weighted),
                'f1_score': float(f1_weighted),
                'confusion_matrix': json.dumps(conf_matrix.tolist()),
                'feature_importance': json.dumps(feature_importance_dict),
                'dataset_size': len(df),
            }
            if hasattr(MLMetrics, 'notes'):
                metrics_kwargs['notes'] = json.dumps(notes)

            metrics = MLMetrics(**metrics_kwargs)

            db.session.add(metrics)
            db.session.commit()

            print("Metrics saved to database")
            print(f"  - Model Version: {metrics.model_version}")
            print(f"  - Accuracy: {accuracy:.4f}")
            print(f"  - Precision: {precision_weighted:.4f}")
            print(f"  - Recall: {recall_weighted:.4f}")
            print(f"  - F1-Score: {f1_weighted:.4f}")
            print(f"  - Dataset Size: {metrics.dataset_size}")
            print(f"  - Training Samples: {len(X_train)}")
            print(f"  - Test Samples: {len(X_test)}")
    except Exception as e:
        print(f"⚠ Warning: Could not save to database: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"\nFiles created:")
    print(f"  - Model: {model_path}")
    if plot_path:
        print(f"  - Plot: {plot_path}")
    print(f"\nModel Summary:")
    print(f"  - Algorithm: LightGBM Classifier")
    print(f"  - Dataset Size: {len(df):,} samples")
    print(f"  - Training Samples: {len(X_train):,}")
    print(f"  - Test Samples: {len(X_test):,}")
    print(f"  - Features: {X_train.shape[1]}")
    print(f"  - Classes: {len(label_encoder.classes_)}")
    print(f"  - Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
    
    return {
        'accuracy': accuracy,
        'model_path': model_path,
        'feature_importance': sorted_feature_importance.to_dict()
    }

if __name__ == "__main__":
    result = train_lightgbm_model()
