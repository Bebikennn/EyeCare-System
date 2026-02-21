import pymysql
from config import *

try:
    conn = pymysql.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    cursor = conn.cursor()
    
    # Read and execute SQL file
    with open('sql/create_feedback_table.sql', 'r') as f:
        sql = f.read()
        cursor.execute(sql)
    
    conn.commit()
    print("✅ Feedback table created successfully!")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
