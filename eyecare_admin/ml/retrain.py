import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
import json
from datetime import datetime
import os

from preprocess import DataPreprocessor

class LightGBMRetrainer:
    def __init__(self):
        self.model = None
        self.preprocessor = DataPreprocessor()
        self.feature_names = None
        
    def retrain_model(self, dataset_path, model_save_path='ml/model.pkl'):
        """
        Retrain LightGBM model with new dataset
        
        Parameters:
        - dataset_path: path to CSV file with training data
        - model_save_path: path to save trained model
        
        Returns:
        - metrics: dictionary with model performance metrics
        """
        
        print(f"Loading dataset from {dataset_path}...")
        
        # Load data
        df = pd.read_csv(dataset_path)
        
        print(f"Dataset loaded: {len(df)} records")
        
        # Preprocess data
        print("Preprocessing data...")
        X, y = self.preprocessor.preprocess_data(df, is_training=True)
        
        # Store feature names
        self.feature_names = [
            'age', 'bmi', 'blood_sugar', 'systolic_bp', 'diastolic_bp',
            'smoking', 'alcohol', 'screen_time', 'sleep_hours', 'exercise_frequency',
            'blurred_vision', 'eye_pain', 'redness', 'dry_eyes',
            'age_bmi_interaction', 'screen_sleep_ratio', 'total_symptoms', 'lifestyle_risk'
        ]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Create LightGBM datasets
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=self.feature_names)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data, feature_name=self.feature_names)
        
        # LightGBM parameters
        params = {
            'objective': 'multiclass',
            'num_class': 3,  # low, moderate, high
            'boosting_type': 'gbdt',
            'metric': 'multi_logloss',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': 0,
            'max_depth': 6,
            'min_data_in_leaf': 20
        }
        
        # Train model
        print("Training LightGBM model...")
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[test_data],
            callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(period=20)]
        )
        
        print("Training completed!")
        
        # Evaluate model
        print("Evaluating model...")
        metrics = self.evaluate_model(X_test, y_test)
        
        # Save model
        print(f"Saving model to {model_save_path}...")
        self.save_model(model_save_path)
        
        # Save preprocessor
        self.preprocessor.save_preprocessor()
        
        return metrics
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate model and return metrics"""
        
        # Predictions
        y_pred_proba = self.model.predict(X_test)
        y_pred = np.argmax(y_pred_proba, axis=1)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        # Feature importance
        feature_importance = dict(zip(self.feature_names, self.model.feature_importance().tolist()))
        
        # Normalize feature importance
        total_importance = sum(feature_importance.values())
        feature_importance = {k: v/total_importance for k, v in feature_importance.items()}
        
        # Sort by importance
        feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': cm.tolist(),
            'feature_importance': feature_importance,
            'dataset_size': len(X_test) * 5,  # Approximate total size
            'model_version': f'LightGBM-v{datetime.now().strftime("%Y%m%d%H%M")}'
        }
        
        print("\n=== Model Performance ===")
        print(f"Accuracy: {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall: {recall:.4f}")
        print(f"F1 Score: {f1:.4f}")
        print("\nConfusion Matrix:")
        print(cm)
        print("\nTop 5 Important Features:")
        for i, (feature, importance) in enumerate(list(feature_importance.items())[:5], 1):
            print(f"{i}. {feature}: {importance:.4f}")
        
        return metrics
    
    def save_model(self, filepath='ml/model.pkl'):
        """Save trained model"""
        joblib.dump(self.model, filepath)
        print(f"Model saved to {filepath}")
    
    def load_model(self, filepath='ml/model.pkl'):
        """Load trained model"""
        self.model = joblib.load(filepath)
        print(f"Model loaded from {filepath}")

def retrain_from_assessments_db():
    """
    Retrain model using assessments from database
    This function can be called from the Flask API
    """
    from database import db, Assessment
    
    # Query assessments
    assessments = Assessment.query.filter(Assessment.risk_level.isnot(None)).all()
    
    if len(assessments) < 50:
        return {
            'error': 'Insufficient data for retraining. Need at least 50 labeled assessments.'
        }
    
    # Convert to DataFrame
    data = []
    for a in assessments:
        data.append({
            'age': a.age,
            'bmi': a.bmi,
            'blood_pressure': a.blood_pressure,
            'blood_sugar': a.blood_sugar,
            'smoking': a.smoking,
            'alcohol': a.alcohol,
            'screen_time': a.screen_time,
            'sleep_hours': a.sleep_hours,
            'exercise_frequency': a.exercise_frequency,
            'blurred_vision': a.blurred_vision,
            'eye_pain': a.eye_pain,
            'redness': a.redness,
            'dry_eyes': a.dry_eyes,
            'risk_level': a.risk_level
        })
    
    df = pd.DataFrame(data)
    
    # Save to temporary CSV
    temp_path = 'ml/datasets/temp_training_data.csv'
    os.makedirs(os.path.dirname(temp_path), exist_ok=True)
    df.to_csv(temp_path, index=False)
    
    # Retrain
    retrainer = LightGBMRetrainer()
    metrics = retrainer.retrain_model(temp_path)
    
    return metrics

if __name__ == '__main__':
    # Example usage
    retrainer = LightGBMRetrainer()
    
    # Create sample dataset if not exists
    sample_dataset_path = 'ml/datasets/sample_data.csv'
    
    if not os.path.exists(sample_dataset_path):
        print("Creating sample dataset...")
        
        # Generate synthetic data
        np.random.seed(42)
        n_samples = 500
        
        data = {
            'age': np.random.randint(20, 80, n_samples),
            'bmi': np.random.uniform(18, 35, n_samples),
            'blood_pressure': [f"{np.random.randint(90, 160)}/{np.random.randint(60, 100)}" for _ in range(n_samples)],
            'blood_sugar': np.random.uniform(70, 140, n_samples),
            'smoking': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'alcohol': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
            'screen_time': np.random.uniform(2, 12, n_samples),
            'sleep_hours': np.random.uniform(4, 10, n_samples),
            'exercise_frequency': np.random.randint(0, 7, n_samples),
            'blurred_vision': np.random.choice([0, 1], n_samples, p=[0.7, 0.3]),
            'eye_pain': np.random.choice([0, 1], n_samples, p=[0.8, 0.2]),
            'redness': np.random.choice([0, 1], n_samples, p=[0.75, 0.25]),
            'dry_eyes': np.random.choice([0, 1], n_samples, p=[0.6, 0.4]),
            'risk_level': np.random.choice(['low', 'moderate', 'high'], n_samples, p=[0.5, 0.3, 0.2])
        }
        
        df = pd.DataFrame(data)
        os.makedirs(os.path.dirname(sample_dataset_path), exist_ok=True)
        df.to_csv(sample_dataset_path, index=False)
        print(f"Sample dataset created: {sample_dataset_path}")
    
    # Retrain model
    metrics = retrainer.retrain_model(sample_dataset_path)
    
    print("\n=== Retraining Complete ===")
    print(json.dumps(metrics, indent=2))
