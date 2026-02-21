import requests
import json

# Test feedback submission
url = "http://192.168.100.17:5000/feedback"

test_data = {
    "user_id": "test_user_123",
    "username": "Test User",
    "email": "test@example.com",
    "rating": 5,
    "category": "Assessment Accuracy",
    "comment": "Great app! The assessment was very accurate and helpful."
}

try:
    response = requests.post(url, json=test_data, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
