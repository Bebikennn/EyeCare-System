import requests
import json

# Test login endpoint
url = "http://localhost:5000/login"
data = {
    "email": "test@eyecare.com",
    "password": "testpass123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
