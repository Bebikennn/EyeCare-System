"""
EyeCare Backend Tests - Assessment Module
"""
import pytest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_assessment():
    """Sample assessment data."""
    return {
        "user_id": "test-user-001",
        "Age": 25,
        "Gender": "Male",
        "BMI": 22.5,
        "Screen_Time_Hours": 6.0,
        "Sleep_Hours": 7.0,
        "Smoker": "No",
        "Alcohol_Use": "No",
        "Diabetes": "No",
        "Hypertension": "No",
        "Family_History_Eye_Disease": "No",
        "Eye_Pain_Frequency": 2,
        "Blurry_Vision_Score": 3,
        "Light_Sensitivity": "No",
        "Eye_Strains_Per_Day": 2,
        "Outdoor_Exposure_Hours": 2.0,
        "Diet_Score": 7,
        "Water_Intake_Liters": 2.5,
        "Glasses_Usage": "Yes",
        "Previous_Eye_Surgery": "No",
        "Physical_Activity_Level": "Moderate"
    }

# ===========================================
# Assessment Submission Tests
# ===========================================

def test_submit_assessment_missing_data(client):
    """Test assessment submission with missing data."""
    response = client.post('/api/assessment/submit',
        json={"user_id": "test-user"},
        content_type='application/json'
    )
    # Should return error or handle gracefully
    assert response.status_code in [400, 500]

def test_submit_assessment_invalid_user_id(client):
    """Test assessment submission with invalid user ID."""
    response = client.post('/api/assessment/submit',
        json={"user_id": ""},
        content_type='application/json'
    )
    assert response.status_code in [400, 500]

# ===========================================
# Assessment History Tests
# ===========================================

def test_get_history_missing_user(client):
    """Test getting history for non-existent user."""
    response = client.get('/api/assessment/history/nonexistent-user-id')
    # Should return empty history or 404
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))

def test_get_history_format(client):
    """Test history response format."""
    response = client.get('/api/assessment/history/test-user-001')
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = json.loads(response.data)
        # Should return a list or dict with proper structure
        assert isinstance(data, (list, dict))

# ===========================================
# ML Prediction Tests
# ===========================================

def test_ml_model_exists():
    """Test that ML model file exists."""
    from pathlib import Path
    model_path = Path(__file__).parent.parent / 'models' / 'lightgbm_model.pkl'
    assert model_path.exists(), "ML model file not found"

def test_ml_prediction_service():
    """Test ML prediction service can load."""
    try:
        from services.ml_predict import load_model
        model_data = load_model()
        assert model_data is not None
        assert 'model' in model_data
        assert 'encoders' in model_data
    except FileNotFoundError:
        pytest.skip("ML model not found")
    except Exception as e:
        pytest.fail(f"ML prediction service failed: {str(e)}")

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
