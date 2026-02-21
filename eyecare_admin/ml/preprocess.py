import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib

class DataPreprocessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
    def preprocess_data(self, df, is_training=True):
        """
        Preprocess data for LightGBM model
        
        Parameters:
        - df: pandas DataFrame with raw data
        - is_training: boolean, True if preprocessing training data
        
        Returns:
        - X: preprocessed features
        - y: encoded labels (only if is_training=True)
        """
        
        # Create a copy to avoid modifying original
        data = df.copy()
        
        # Handle missing values
        numeric_cols = ['age', 'bmi', 'blood_sugar', 'screen_time', 'sleep_hours', 'exercise_frequency']
        for col in numeric_cols:
            if col in data.columns:
                data[col].fillna(data[col].median(), inplace=True)
        
        # Parse blood pressure if it's a string
        if 'blood_pressure' in data.columns and data['blood_pressure'].dtype == 'object':
            # Extract systolic pressure
            data['systolic_bp'] = data['blood_pressure'].str.split('/').str[0].astype(float)
            data['diastolic_bp'] = data['blood_pressure'].str.split('/').str[1].astype(float)
            data.drop('blood_pressure', axis=1, inplace=True)
        
        # Convert boolean columns
        boolean_cols = ['smoking', 'alcohol', 'blurred_vision', 'eye_pain', 'redness', 'dry_eyes']
        for col in boolean_cols:
            if col in data.columns:
                data[col] = data[col].astype(int)
        
        # Feature engineering
        if 'age' in data.columns and 'bmi' in data.columns:
            data['age_bmi_interaction'] = data['age'] * data['bmi']
        
        if 'screen_time' in data.columns and 'sleep_hours' in data.columns:
            data['screen_sleep_ratio'] = data['screen_time'] / (data['sleep_hours'] + 0.1)
        
        # Calculate total symptom score
        symptom_cols = [col for col in boolean_cols if col in data.columns and col.endswith(('_vision', '_pain', '_eyes', 'redness'))]
        if symptom_cols:
            data['total_symptoms'] = data[symptom_cols].sum(axis=1)
        
        # Risk score calculation
        if 'smoking' in data.columns and 'alcohol' in data.columns:
            data['lifestyle_risk'] = data['smoking'] + data['alcohol']
        
        # Select features for model
        feature_cols = [
            'age', 'bmi', 'blood_sugar', 'systolic_bp', 'diastolic_bp',
            'smoking', 'alcohol', 'screen_time', 'sleep_hours', 'exercise_frequency',
            'blurred_vision', 'eye_pain', 'redness', 'dry_eyes',
            'age_bmi_interaction', 'screen_sleep_ratio', 'total_symptoms', 'lifestyle_risk'
        ]
        
        # Filter only existing columns
        feature_cols = [col for col in feature_cols if col in data.columns]
        
        X = data[feature_cols]
        
        # Scale features
        if is_training:
            X_scaled = self.scaler.fit_transform(X)
            
            # Encode target if training
            if 'risk_level' in data.columns:
                y = self.label_encoder.fit_transform(data['risk_level'])
                return X_scaled, y
            
            return X_scaled, None
        else:
            X_scaled = self.scaler.transform(X)
            return X_scaled
    
    def save_preprocessor(self, filepath='ml/preprocessor.pkl'):
        """Save scaler and label encoder"""
        joblib.dump({
            'scaler': self.scaler,
            'label_encoder': self.label_encoder
        }, filepath)
        print(f"Preprocessor saved to {filepath}")
    
    def load_preprocessor(self, filepath='ml/preprocessor.pkl'):
        """Load scaler and label encoder"""
        data = joblib.load(filepath)
        self.scaler = data['scaler']
        self.label_encoder = data['label_encoder']
        print(f"Preprocessor loaded from {filepath}")

def preprocess_single_assessment(assessment_data):
    """
    Preprocess a single assessment for prediction
    
    Parameters:
    - assessment_data: dict with assessment fields
    
    Returns:
    - preprocessed numpy array
    """
    
    # Convert to DataFrame
    df = pd.DataFrame([assessment_data])
    
    # Load preprocessor
    preprocessor = DataPreprocessor()
    try:
        preprocessor.load_preprocessor()
    except:
        print("Warning: Preprocessor not found, using default scaling")
    
    # Preprocess
    X = preprocessor.preprocess_data(df, is_training=False)
    
    return X

if __name__ == '__main__':
    # Example usage
    sample_data = {
        'age': 45,
        'bmi': 28.5,
        'blood_pressure': '140/90',
        'blood_sugar': 110,
        'smoking': True,
        'alcohol': False,
        'screen_time': 8,
        'sleep_hours': 6,
        'exercise_frequency': 2,
        'blurred_vision': True,
        'eye_pain': False,
        'redness': False,
        'dry_eyes': True
    }
    
    result = preprocess_single_assessment(sample_data)
    print("Preprocessed features shape:", result.shape)
    print("Preprocessed features:", result)
