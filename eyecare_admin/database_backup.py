"""
Automated Database Backup Script
Backs up MySQL database with timestamp and compression
"""
import pymysql
import subprocess
import os
from datetime import datetime
from config import DB_CONFIG
import gzip
import shutil

BACKUP_DIR = "backups"
MAX_BACKUPS = 30  # Keep last 30 backups

def create_backup():
    """Create a timestamped database backup"""
    
    # Create backups directory
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"eyecare_db_backup_{timestamp}.sql"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    compressed_path = f"{backup_path}.gz"
    
    print("=" * 70)
    print("DATABASE BACKUP")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['database']}")
    print(f"Host: {DB_CONFIG['host']}")
    print(f"Backup file: {backup_filename}")
    print()
    
    try:
        # Method 1: Using mysqldump (preferred if available)
        try:
            # Build mysqldump command
            password_arg = f"-p{DB_CONFIG['password']}" if DB_CONFIG['password'] else ""
            
            cmd = [
                'mysqldump',
                f"-h{DB_CONFIG['host']}",
                f"-u{DB_CONFIG['user']}",
                password_arg,
                '--single-transaction',
                '--routines',
                '--triggers',
                '--events',
                DB_CONFIG['database']
            ]
            
            # Remove empty password arg
            cmd = [c for c in cmd if c]
            
            print("Using mysqldump method...")
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                raise Exception(f"mysqldump failed: {result.stderr}")
            
            print(f"✓ Backup created: {backup_filename}")
            
        except FileNotFoundError:
            # Method 2: Using Python if mysqldump not available
            print("mysqldump not found, using Python method...")
            backup_with_python(backup_path)
        
        # Compress the backup
        print("Compressing backup...")
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove uncompressed file
        os.remove(backup_path)
        
        # Get file size
        size_mb = os.path.getsize(compressed_path) / (1024 * 1024)
        print(f"✓ Compressed: {backup_filename}.gz ({size_mb:.2f} MB)")
        
        # Clean old backups
        cleanup_old_backups()
        
        print()
        print("=" * 70)
        print("✓ BACKUP COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Location: {os.path.abspath(compressed_path)}")
        print()
        
        return compressed_path
        
    except Exception as e:
        print(f"✗ ERROR: Backup failed - {str(e)}")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        return None

def backup_with_python(backup_path):
    """Backup database using Python (fallback method)"""
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    with open(backup_path, 'w') as f:
        # Write header
        f.write(f"-- MySQL Database Backup\n")
        f.write(f"-- Generated: {datetime.now()}\n")
        f.write(f"-- Database: {DB_CONFIG['database']}\n\n")
        
        # Get all tables
        cur.execute("SHOW TABLES")
        tables = [row[0] for row in cur.fetchall()]
        
        for table in tables:
            print(f"  Backing up table: {table}...")
            
            # Table structure
            cur.execute(f"SHOW CREATE TABLE {table}")
            create_table = cur.fetchone()[1]
            f.write(f"\n-- Table: {table}\n")
            f.write(f"DROP TABLE IF EXISTS `{table}`;\n")
            f.write(f"{create_table};\n\n")
            
            # Table data
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            
            if rows:
                # Get column names
                cur.execute(f"DESCRIBE {table}")
                columns = [col[0] for col in cur.fetchall()]
                
                f.write(f"-- Data for table {table}\n")
                f.write(f"INSERT INTO `{table}` ({', '.join([f'`{c}`' for c in columns])}) VALUES\n")
                
                for i, row in enumerate(rows):
                    values = []
                    for val in row:
                        if val is None:
                            values.append('NULL')
                        elif isinstance(val, (int, float)):
                            values.append(str(val))
                        else:
                            # Escape single quotes
                            escaped = str(val).replace("'", "''")
                            values.append(f"'{escaped}'")
                    
                    if i < len(rows) - 1:
                        f.write(f"({', '.join(values)}),\n")
                    else:
                        f.write(f"({', '.join(values)});\n")
                
                f.write("\n")
    
    conn.close()
    print(f"✓ Backup created using Python method")

def cleanup_old_backups():
    """Remove old backups, keeping only MAX_BACKUPS most recent"""
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.sql.gz')]
    backups.sort(reverse=True)  # Newest first
    
    if len(backups) > MAX_BACKUPS:
        removed = 0
        for old_backup in backups[MAX_BACKUPS:]:
            os.remove(os.path.join(BACKUP_DIR, old_backup))
            removed += 1
        print(f"✓ Cleaned up {removed} old backup(s)")

def restore_backup(backup_file):
    """Restore database from backup file"""
    if not os.path.exists(backup_file):
        print(f"✗ ERROR: Backup file not found: {backup_file}")
        return False
    
    print("=" * 70)
    print("DATABASE RESTORE")
    print("=" * 70)
    print(f"Backup file: {backup_file}")
    print()
    print("⚠️  WARNING: This will overwrite the current database!")
    
    # Uncompress if needed
    if backup_file.endswith('.gz'):
        print("Decompressing backup...")
        sql_file = backup_file[:-3]  # Remove .gz
        with gzip.open(backup_file, 'rb') as f_in:
            with open(sql_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    else:
        sql_file = backup_file
    
    try:
        # Restore using mysql command
        password_arg = f"-p{DB_CONFIG['password']}" if DB_CONFIG['password'] else ""
        
        cmd = [
            'mysql',
            f"-h{DB_CONFIG['host']}",
            f"-u{DB_CONFIG['user']}",
            password_arg,
            DB_CONFIG['database']
        ]
        
        cmd = [c for c in cmd if c]
        
        with open(sql_file, 'r') as f:
            result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            raise Exception(f"mysql restore failed: {result.stderr}")
        
        print("✓ Database restored successfully")
        
        # Remove decompressed file if it was created
        if backup_file.endswith('.gz') and os.path.exists(sql_file):
            os.remove(sql_file)
        
        return True
        
    except Exception as e:
        print(f"✗ ERROR: Restore failed - {str(e)}")
        return False

def list_backups():
    """List all available backups"""
    if not os.path.exists(BACKUP_DIR):
        print("No backups found")
        return []
    
    backups = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.sql.gz')]
    backups.sort(reverse=True)
    
    print("=" * 70)
    print("AVAILABLE BACKUPS")
    print("=" * 70)
    for i, backup in enumerate(backups, 1):
        path = os.path.join(BACKUP_DIR, backup)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        mtime = datetime.fromtimestamp(os.path.getmtime(path))
        print(f"{i}. {backup} - {size_mb:.2f} MB - {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return backups

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) > 2:
            restore_backup(sys.argv[2])
        else:
            list_backups()
            print("\nUsage: python database_backup.py restore <backup_file>")
    elif len(sys.argv) > 1 and sys.argv[1] == 'list':
        list_backups()
    else:
        create_backup()
