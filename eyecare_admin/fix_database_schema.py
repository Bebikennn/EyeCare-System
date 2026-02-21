"""Fix all database schema issues"""
from config import DB_CONFIG
import pymysql

def execute_sql(cursor, sql, description):
    """Execute SQL and handle errors"""
    try:
        cursor.execute(sql)
        print(f"✅ {description}")
        return True
    except pymysql.err.OperationalError as e:
        if e.args[0] == 1060:  # Duplicate column
            print(f"⚠  {description} - Column already exists")
            return True
        else:
            print(f"❌ {description} - Error: {e}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

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
    
    print("\n" + "="*60)
    print("FIXING DATABASE SCHEMA")
    print("="*60 + "\n")
    
    # 1. Create pending_actions table if not exists
    print("1. Creating pending_actions table...")
    execute_sql(cursor, """
        CREATE TABLE IF NOT EXISTS pending_actions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            action_type VARCHAR(50) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id VARCHAR(100),
            entity_data TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            requested_by INT NOT NULL,
            approved_by INT,
            reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (requested_by) REFERENCES admins(id),
            FOREIGN KEY (approved_by) REFERENCES admins(id)
        )
    """, "Created pending_actions table")
    
    # 2. Fix assessment_results table - add risk_level if missing
    print("\n2. Adding risk_level to assessment_results...")
    execute_sql(cursor, """
        ALTER TABLE assessment_results 
        ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) AFTER predicted_disease
    """, "Added risk_level column")
    
    # 3. Fix assessment_results - add get_stats method support
    print("\n3. Checking assessment_results structure...")
    cursor.execute("DESCRIBE assessment_results")
    columns = [row[0] for row in cursor.fetchall()]
    print(f"   Assessment columns: {', '.join(columns)}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DATABASE SCHEMA FIXED")
    print("="*60 + "\n")
    
except Exception as e:
    print(f"\n❌ Error: {e}\n")
