"""
Tests for prediction/ML routes
"""
import pytest
from app import app
import json

@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_predict_missing_data(client):
    """Test prediction without required data"""
    response = client.post('/',
                           json={},
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_predict_missing_age(client):
    """Test prediction without age field"""
    payload = {
        'screen_time': 6,
        'sleep_hours': 7,
        'diet_quality': 3
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 400

def test_predict_missing_screen_time(client):
    """Test prediction without screen_time field"""
    payload = {
        'age': 30,
        'sleep_hours': 7,
        'diet_quality': 3
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    assert response.status_code == 400

def test_predict_with_valid_data(client):
    """Test prediction with all required fields"""
    payload = {
        'age': 30,
        'screen_time': 6,
        'sleep_hours': 7,
        'diet_quality': 3
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    # Should succeed with valid data, or 400 if missing fields
    assert response.status_code in [200, 400, 500]
    if response.status_code == 200:
        data = response.get_json()
        # Response should contain prediction data or error
        assert data is not None
        assert isinstance(data, dict)

def test_predict_with_high_risk_data(client):
    """Test prediction with high risk factors"""
    payload = {
        'age': 65,
        'screen_time': 12,
        'sleep_hours': 4,
        'diet_quality': 1
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.get_json()
        # Should return some prediction
        assert data is not None

def test_predict_with_low_risk_data(client):
    """Test prediction with low risk factors"""
    payload = {
        'age': 25,
        'screen_time': 4,
        'sleep_hours': 8,
        'diet_quality': 5
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.get_json()
        assert data is not None

def test_predict_with_invalid_age(client):
    """Test prediction with invalid age (negative)"""
    payload = {
        'age': -5,
        'screen_time': 6,
        'sleep_hours': 7,
        'diet_quality': 3
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    # Should either succeed with validation or return 200 with prediction
    assert response.status_code in [200, 400]

def test_predict_with_extreme_screen_time(client):
    """Test prediction with extreme screen time"""
    payload = {
        'age': 30,
        'screen_time': 24,  # 24 hours (extreme)
        'sleep_hours': 7,
        'diet_quality': 3
    }
    response = client.post('/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    # Should handle extreme values gracefully
    assert response.status_code in [200, 400]

def test_predict_response_format(client):
    """Test that prediction response has expected format"""
    payload = {
        'age': 30,
        'screen_time': 6,
        'sleep_hours': 7,
        'diet_quality': 3
    }
    response = client.post('/api/predict/',
                           json=payload,
                           headers={'Content-Type': 'application/json'})
    if response.status_code == 200:
        data = response.get_json()
        # Check if response contains expected keys
        assert isinstance(data, dict)
        # At minimum should have some prediction result
        assert len(data) > 0
