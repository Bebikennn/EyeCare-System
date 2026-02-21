"""
Smoke Test Suite for EyeCare Admin Dashboard
Tests all main endpoints to verify system health
"""
import requests
import json
from datetime import datetime
import sys

BASE_URL = "http://127.0.0.1:5001"
session = requests.Session()

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def test_endpoint(name, method, endpoint, expected_status=200, data=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = session.get(url, timeout=5)
        elif method == "POST":
            response = session.post(url, json=data, timeout=5)
        else:
            response = session.request(method, url, json=data, timeout=5)
        
        if response.status_code == expected_status:
            print_success(f"{name}: {response.status_code} (Expected: {expected_status})")
            return True, response
        else:
            print_error(f"{name}: {response.status_code} (Expected: {expected_status})")
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('error', 'Unknown error')}")
                except:
                    print(f"   Response: {response.text[:200]}")
            return False, response
    except requests.exceptions.RequestException as e:
        print_error(f"{name}: Connection failed - {str(e)}")
        return False, None

def login():
    """Login to get session"""
    print_header("Authentication Test")
    data = {
        "username": "admin",
        "password": "admin123"
    }
    success, response = test_endpoint("Login", "POST", "/api/auth/login", 200, data)
    if success:
        print("   Session established")
    return success

def test_users_endpoints():
    """Test all user-related endpoints"""
    print_header("Users Endpoints")
    
    results = []
    results.append(test_endpoint("Users List", "GET", "/api/users/?page=1&per_page=10"))
    results.append(test_endpoint("Users Stats", "GET", "/api/users/stats"))
    results.append(test_endpoint("Recent Users", "GET", "/api/users/recent?limit=5"))
    results.append(test_endpoint("Archived Users", "GET", "/api/users/archived?page=1&per_page=5"))
    
    return all(r[0] for r in results)

def test_assessments_endpoints():
    """Test assessment-related endpoints"""
    print_header("Assessments Endpoints")
    
    results = []
    results.append(test_endpoint("Assessments List", "GET", "/api/assessments/?page=1&per_page=10"))
    results.append(test_endpoint("Assessments Stats", "GET", "/api/assessments/stats"))
    
    return all(r[0] for r in results)

def test_approvals_endpoints():
    """Test approval-related endpoints"""
    print_header("Approvals Endpoints")
    
    results = []
    results.append(test_endpoint("Approvals List", "GET", "/api/approvals/"))
    results.append(test_endpoint("My Requests", "GET", "/api/approvals/my-requests"))
    results.append(test_endpoint("Approvals Analytics", "GET", "/api/approvals/analytics"))
    
    return all(r[0] for r in results)

def test_ml_endpoints():
    """Test ML-related endpoints"""
    print_header("ML Analytics Endpoints")
    
    results = []
    results.append(test_endpoint("ML Metrics", "GET", "/api/ml/metrics"))
    
    return all(r[0] for r in results)

def test_healthtips_endpoints():
    """Test health tips endpoints"""
    print_header("Health Tips Endpoints")
    
    results = []
    results.append(test_endpoint("Health Tips List", "GET", "/api/healthtips/?page=1&per_page=10"))
    
    return all(r[0] for r in results)

def test_notifications_endpoints():
    """Test notification endpoints"""
    print_header("Notifications Endpoints")
    
    results = []
    results.append(test_endpoint("Notifications List", "GET", "/api/notifications/?limit=10"))
    results.append(test_endpoint("Unread Notifications", "GET", "/api/notifications/?unread_only=true"))
    
    return all(r[0] for r in results)

def test_admin_endpoints():
    """Test admin management endpoints"""
    print_header("Admin Management Endpoints")
    
    results = []
    results.append(test_endpoint("Admin List", "GET", "/api/admin/"))
    
    return all(r[0] for r in results)

def test_logs_endpoints():
    """Test activity logs endpoints"""
    print_header("Activity Logs Endpoints")
    
    results = []
    results.append(test_endpoint("Recent Logs", "GET", "/api/logs/recent?limit=5"))
    results.append(test_endpoint("Logs List", "GET", "/api/logs/?page=1&per_page=20"))
    
    return all(r[0] for r in results)

def main():
    """Run all smoke tests"""
    print(f"\n{BLUE}{'='*60}")
    print(f"  EyeCare Admin Dashboard - Smoke Test Suite")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}\n")
    
    print(f"Testing server at: {BASE_URL}")
    
    # Test server availability
    try:
        response = requests.get(BASE_URL + "/dashboard", timeout=5)
        if response.status_code == 200:
            print_success("Server is running")
        else:
            print_warning(f"Server returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot connect to server: {e}")
        print("\nPlease ensure the server is running with START_ADMIN.bat")
        sys.exit(1)
    
    # Login first
    if not login():
        print_error("Login failed - cannot continue tests")
        sys.exit(1)
    
    # Run all endpoint tests
    results = {
        "Users": test_users_endpoints(),
        "Assessments": test_assessments_endpoints(),
        "Approvals": test_approvals_endpoints(),
        "ML Analytics": test_ml_endpoints(),
        "Health Tips": test_healthtips_endpoints(),
        "Notifications": test_notifications_endpoints(),
        "Admin Management": test_admin_endpoints(),
        "Activity Logs": test_logs_endpoints()
    }
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for category, passed_test in results.items():
        if passed_test:
            print_success(f"{category}: PASSED")
        else:
            print_error(f"{category}: FAILED")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    if passed == total:
        print(f"{GREEN}All tests passed! ({passed}/{total}){RESET}")
        sys.exit(0)
    else:
        print(f"{YELLOW}Some tests failed ({passed}/{total} passed){RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
