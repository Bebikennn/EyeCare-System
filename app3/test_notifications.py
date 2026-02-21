#!/usr/bin/env python3
"""
Notification System Test Script
Tests all notification endpoints
"""

import requests
import json
import uuid
from datetime import datetime

BASE_URL = "http://192.168.1.11:5000"

# Use a test user ID (replace with actual user ID)
TEST_USER_ID = "test-user-123"

def test_create_notification():
    """Test creating a new notification"""
    print("\n" + "="*60)
    print("TEST 1: Create Notification")
    print("="*60)
    
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/create"
    
    payload = {
        "title": "Welcome to Notifications! 🔔",
        "message": "The notification system is now active and working",
        "type": "success",
        "link": "/dashboard"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 201
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_create_multiple_notifications():
    """Test creating multiple notifications of different types"""
    print("\n" + "="*60)
    print("TEST 2: Create Multiple Notifications (Different Types)")
    print("="*60)
    
    notifications = [
        {
            "title": "Assessment Completed ✓",
            "message": "Your eye health assessment has been saved successfully",
            "type": "success"
        },
        {
            "title": "Daily Health Tip 💡",
            "message": "Remember to take regular eye breaks every 20 minutes",
            "type": "info"
        },
        {
            "title": "Important Update ⚠️",
            "message": "Please review your profile settings",
            "type": "warning"
        },
        {
            "title": "System Error ❌",
            "message": "Unable to sync data. Please check your connection",
            "type": "error"
        }
    ]
    
    results = []
    for notif in notifications:
        url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/create"
        try:
            response = requests.post(url, json=notif, timeout=10)
            status = response.status_code == 201
            results.append(status)
            print(f"✓ {notif['title']}: {'SUCCESS' if status else 'FAILED'}")
        except Exception as e:
            print(f"✗ {notif['title']}: ERROR - {e}")
            results.append(False)
    
    print(f"\nResults: {sum(results)}/{len(results)} notifications created")
    return all(results)

def test_get_notifications():
    """Test fetching all notifications for user"""
    print("\n" + "="*60)
    print("TEST 3: Get All User Notifications")
    print("="*60)
    
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        
        print(f"\nResponse Summary:")
        print(f"  Status: {data.get('status')}")
        print(f"  Total Notifications: {len(data.get('notifications', []))}")
        print(f"  Unread Count: {data.get('unread_count', 0)}")
        
        if data.get('notifications'):
            print(f"\nNotifications:")
            for notif in data['notifications'][:3]:  # Show first 3
                print(f"  - [{notif['type'].upper()}] {notif['title']}")
                print(f"    Message: {notif['message'][:50]}...")
                print(f"    Read: {notif['is_read']}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_mark_notification_read():
    """Test marking a notification as read"""
    print("\n" + "="*60)
    print("TEST 4: Mark Notification as Read")
    print("="*60)
    
    # First get notifications
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}"
    try:
        response = requests.get(url, timeout=10)
        notifications = response.json().get('notifications', [])
        
        if not notifications:
            print("No notifications available to mark as read")
            return False
        
        # Get first unread notification
        unread_notif = next((n for n in notifications if not n['is_read']), notifications[0])
        notif_id = unread_notif['notification_id']
        
        # Mark as read
        mark_url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/{notif_id}/mark-read"
        response = requests.put(mark_url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Notification ID: {notif_id}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_mark_all_read():
    """Test marking all notifications as read"""
    print("\n" + "="*60)
    print("TEST 5: Mark All Notifications as Read")
    print("="*60)
    
    url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}/mark-all-read"
    
    try:
        response = requests.put(url, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        # Verify unread count is now 0
        if response.status_code == 200:
            verify_url = f"{BASE_URL}/api/notifications/user/{TEST_USER_ID}"
            verify_response = requests.get(verify_url, timeout=10)
            unread_count = verify_response.json().get('unread_count', 0)
            print(f"\nVerification: Unread count = {unread_count}")
            return unread_count == 0
        
        return response.status_code == 200
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def run_all_tests():
    """Run all notification tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║  " + "NOTIFICATION SYSTEM - COMPREHENSIVE TEST SUITE".center(54) + "  ║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    print(f"\nTest User ID: {TEST_USER_ID}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Create Notification": test_create_notification(),
        "Create Multiple Notifications": test_create_multiple_notifications(),
        "Get All Notifications": test_get_notifications(),
        "Mark Notification as Read": test_mark_notification_read(),
        "Mark All as Read": test_mark_all_read(),
    }
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:.<45} {status}")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Notification system is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the output above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\nFatal error: {e}")
        exit(1)
