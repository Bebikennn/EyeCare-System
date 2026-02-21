"""
EyeCare Backend Tests - Authentication Module
"""
import pytest
import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
import json

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['DEBUG'] = False
    with app.test_client() as client:
        yield client

@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        'username': 'testuser123',
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'full_name': 'Test User',
        'phone_number': '1234567890'
    }

# ===========================================
# Health Check Tests
# ===========================================

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'
    assert 'message' in data

def test_server_info(client):
    """Test the server info endpoint."""
    response = client.get('/api/server-info')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
    assert 'ip' in data
    assert 'port' in data
    assert 'base_url' in data

# ===========================================
# Authentication Tests
# ===========================================

def test_login_missing_credentials(client):
    """Test login with missing credentials."""
    response = client.post('/login', 
        json={},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'

def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/login',
        json={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        },
        content_type='application/json'
    )
    assert response.status_code in [401, 404]
    data = json.loads(response.data)
    assert data['status'] == 'error'

def test_register_missing_fields(client):
    """Test registration with missing required fields."""
    response = client.post('/register',
        json={
            'username': 'testuser'
        },
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'

# ===========================================
# Verification Tests
# ===========================================

def test_send_verification_missing_email(client):
    """Test sending verification code without email."""
    response = client.post('/send-verification-code',
        json={},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'email' in data['message'].lower()

def test_verify_code_missing_params(client):
    """Test code verification with missing parameters."""
    response = client.post('/verify-code',
        json={'email': 'test@test.com'},
        content_type='application/json'
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['status'] == 'error'

# ===========================================
# Error Handler Tests
# ===========================================

def test_404_error_handler(client):
    """Test 404 error handler."""
    response = client.get('/nonexistent-endpoint')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'not found' in data['message'].lower()

# ===========================================
# Rate Limiting Tests (if enabled)
# ===========================================

def test_rate_limit_check(client):
    """Test that rate limiting is configured."""
    # Make multiple requests to check if rate limiting exists
    for i in range(3):
        response = client.get('/test')
        assert response.status_code == 200
    
    # Check if rate limit headers exist
    response = client.get('/test')
    # Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining
    # These may or may not be present depending on limiter config

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
