"""Add must_change_password column to admins table"""
from config import DB_CONFIG
import pymysql

try:
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        database=DB_CONFIG['database'],
        charset=DB_CONFIG['charset']
    )
    cursor = conn.cursor()
    
    print("Adding must_change_password column to admins table...")
    
    # Check if column exists
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'admins' 
        AND COLUMN_NAME = 'must_change_password'
    """, (DB_CONFIG['database'],))
    
    exists = cursor.fetchone()[0]
    
    if exists:
        print("✅ Column already exists")
    else:
        # Add the column
        cursor.execute("""
            ALTER TABLE admins 
            ADD COLUMN must_change_password TINYINT(1) DEFAULT 0 AFTER status
        """)
        conn.commit()
        print("✅ Column added successfully")
    
    cursor.close()
    conn.close()
    print("\n✅ Migration complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
