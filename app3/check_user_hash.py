import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from eyecare_backend.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def check_user(email):
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB,
        port=MYSQL_PORT,
        cursorclass=pymysql.cursors.DictCursor
    )
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                print(f"User found: {user['username']}")
                print(f"Hash: {user['password_hash']}")
                print(f"Hash length: {len(user['password_hash'])}")
                
                # Test generating a new hash
                test_pass = "test12345"
                new_hash = generate_password_hash(test_pass)
                print(f"New generated hash for 'test12345': {new_hash}")
                print(f"New hash length: {len(new_hash)}")
                
                print(f"Check 'test12345' against new hash: {check_password_hash(new_hash, test_pass)}")
            else:
                print("User not found")
                
    finally:
        conn.close()

if __name__ == "__main__":
    check_user("minatosan0949@gmail.com")
