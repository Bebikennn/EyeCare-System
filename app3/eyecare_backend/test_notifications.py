#!/usr/bin/env python3
"""
Setup test user in the database and run notification tests
"""

import sys
sys.path.insert(0, '.')

from services.db import get_connection
from datetime import datetime
import requests

# Test configuration
TEST_USER_ID = "test_user_123"
BASE_URL = "http://192.168.1.11:5000"

def setup_test_user():
    """Create or verify test user exists in database"""
    print("\n📋 Setting Up Test User...")
    print("-" * 50)
    
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT user_id FROM users WHERE user_id = %s", (TEST_USER_ID,))
            user = cur.fetchone()
            
            if user:
                print(f"✅ Test user '{TEST_USER_ID}' already exists")
            else:
                # Create test user with correct schema
                cur.execute("""
                    INSERT INTO users (user_id, username, email, password_hash, full_name, 
                                      phone_number, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    TEST_USER_ID,
                    "test_user",
                    "test@example.com",
                    "hashed_password_placeholder",
                    "Test User",
                    "1234567890",
                    datetime.now(),
                    datetime.now()
                ))
                conn.commit()
                print(f"✅ Test user '{TEST_USER_ID}' created successfully")
        
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error setting up test user: {str(e)}")
        return False

def test_create_notification():
    """Test: Create a new notification"""
    print("\n🧪 TEST 1: Create Notification")
    print("-" * 50)
    
    payload = {
        "title": "Test Notification",
        "message": "This is a test notification message",
        "type": "success",
        "link": "/dashboard"
    }
    
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/create"
    try:
        response = requests.post(url, json=payload, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ PASSED: Notification created successfully")
            return True
        else:
            print("❌ FAILED: Unexpected status code")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_create_multiple_notifications():
    """Test: Create multiple notifications with different types"""
    print("\n🧪 TEST 2: Create Multiple Notifications")
    print("-" * 50)
    
    notifications = [
        {"title": "Success", "message": "Operation completed", "type": "success"},
        {"title": "Info", "message": "New information available", "type": "info"},
        {"title": "Warning", "message": "Please review this", "type": "warning"},
        {"title": "Error", "message": "Something went wrong", "type": "error"}
    ]
    
    passed = 0
    for notif in notifications:
        try:
            response = requests.post(
                f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/create",
                json=notif,
                timeout=5
            )
            if response.status_code == 201:
                print(f"✅ Created {notif['type']} notification")
                passed += 1
            else:
                print(f"❌ Failed to create {notif['type']} notification")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
    
    if passed == len(notifications):
        print(f"✅ PASSED: All {len(notifications)} notifications created")
        return True
    else:
        print(f"❌ FAILED: Only {passed}/{len(notifications)} created")
        return False

def test_get_user_notifications():
    """Test: Fetch all notifications for user"""
    print("\n🧪 TEST 3: Get User Notifications")
    print("-" * 50)
    
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}"
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        if response.status_code == 200:
            notifications = data.get('notifications', [])
            print(f"Found {len(notifications)} notification(s)")
            for notif in notifications[:3]:  # Show first 3
                print(f"  - {notif.get('title')} ({notif.get('type')})")
            print("✅ PASSED: Successfully retrieved notifications")
            return True
        else:
            print("❌ FAILED: Unexpected status code")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_mark_notification_as_read():
    """Test: Mark a specific notification as read"""
    print("\n🧪 TEST 4: Mark Notification as Read")
    print("-" * 50)
    
    # First get a notification ID
    try:
        response = requests.get(
            f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}",
            timeout=5
        )
        notifications = response.json().get('notifications', [])
        
        if not notifications:
            print("⚠️  No notifications to mark as read")
            return False
        
        notification_id = notifications[0]['notification_id']
        print(f"Marking notification {notification_id} as read...")
        
        update_response = requests.put(
            f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/{notification_id}/mark-read",
            timeout=5
        )
        
        if update_response.status_code == 200:
            result = update_response.json()
            print(f"Result: {result}")
            print("✅ PASSED: Notification marked as read")
            return True
        else:
            print(f"❌ FAILED: Status code {update_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_mark_all_as_read():
    """Test: Mark all notifications as read"""
    print("\n🧪 TEST 5: Mark All Notifications as Read")
    print("-" * 50)
    
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/mark-all-read"
    try:
        response = requests.put(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200:
            updated = data.get('updated_count', 0)
            print(f"✅ PASSED: Marked {updated} notification(s) as read")
            return True
        else:
            print("❌ FAILED: Unexpected status code")
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def run_all_tests():
    """Run all test cases and report results"""
    print("\n" + "="*50)
    print("NOTIFICATION SYSTEM TEST SUITE")
    print("="*50)
    
    # Setup test user first
    if not setup_test_user():
        print("❌ Cannot proceed without test user")
        return False
    
    tests = [
        test_create_notification,
        test_create_multiple_notifications,
        test_get_user_notifications,
        test_mark_notification_as_read,
        test_mark_all_as_read
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR in {test_func.__name__}: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("\n" + "="*50)
    print(f"RESULTS: {passed}/{total} tests passed")
    print("="*50)
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Notification system is working correctly!")
    else:
        print(f"⚠️  {total - passed} test(s) failed - Check errors above")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
