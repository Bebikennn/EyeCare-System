"""
Quick verification that auth.py uses dictionary access correctly
"""
import sys
sys.path.insert(0, 'eyecare_backend')

from services.db import get_connection

# Test database returns dictionaries
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT user_id, username, email FROM users LIMIT 1")
user = cur.fetchone()
conn.close()

if user:
    print("Database returns:", type(user))
    print("Sample user:", user)
    print("\nAccessing fields:")
    print(f"  user['user_id']: {user['user_id']}")
    print(f"  user['username']: {user['username']}")
    print(f"  user['email']: {user['email']}")
    print("\n✅ Dictionary access works correctly!")
else:
    print("No users in database")
