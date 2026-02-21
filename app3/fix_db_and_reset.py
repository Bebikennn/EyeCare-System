import pymysql
from werkzeug.security import generate_password_hash
from eyecare_backend.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

def fix_and_reset(email, new_password):
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
            # 1. Check current column type
            print("Checking 'password_hash' column definition...")
            cursor.execute("SHOW COLUMNS FROM users LIKE 'password_hash'")
            col_def = cursor.fetchone()
            print(f"Current definition: {col_def['Type']}")
            
            # 2. Alter table if needed
            print("Altering 'users' table to increase password_hash length to 255...")
            cursor.execute("ALTER TABLE users MODIFY COLUMN password_hash VARCHAR(255)")
            print("Table altered successfully.")
            
            # 3. Reset password for the user
            print(f"Resetting password for {email}...")
            new_hash = generate_password_hash(new_password)
            cursor.execute("UPDATE users SET password_hash = %s WHERE email = %s", (new_hash, email))
            
            if cursor.rowcount > 0:
                print(f"Password updated successfully for {email}.")
                print(f"New password is: {new_password}")
            else:
                print(f"User {email} not found.")
                
            conn.commit()
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    # Resetting to a simple password for the user to try
    fix_and_reset("minatosan0949@gmail.com", "password123")
