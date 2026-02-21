"""
Database Backup Script for EyeCare Admin
Performs MySQL database backup using mysqldump
"""
import os
import subprocess
from datetime import datetime
from config import DB_CONFIG

# Backup configuration
BACKUP_DIR = os.path.join(os.path.dirname(__file__), '..', 'backups')
MAX_BACKUPS = 30  # Keep last 30 backups

def ensure_backup_directory():
    """Create backup directory if it doesn't exist"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"Created backup directory: {BACKUP_DIR}")

def get_backup_filename():
    """Generate backup filename with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"eyecare_backup_{timestamp}.sql"

def cleanup_old_backups():
    """Remove old backup files, keeping only MAX_BACKUPS most recent"""
    try:
        backup_files = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('eyecare_backup_') and filename.endswith('.sql'):
                filepath = os.path.join(BACKUP_DIR, filename)
                backup_files.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups
        if len(backup_files) > MAX_BACKUPS:
            for filepath, _ in backup_files[MAX_BACKUPS:]:
                os.remove(filepath)
                print(f"Removed old backup: {os.path.basename(filepath)}")
    
    except Exception as e:
        print(f"Warning: Failed to cleanup old backups: {e}")

def backup_database():
    """Backup the MySQL database using mysqldump"""
    try:
        ensure_backup_directory()
        
        backup_file = os.path.join(BACKUP_DIR, get_backup_filename())
        
        # Build mysqldump command
        # Note: Using --single-transaction for InnoDB tables to get consistent backup
        # without locking tables
        cmd = [
            'mysqldump',
            f'--host={DB_CONFIG["host"]}',
            f'--port={DB_CONFIG["port"]}',
            f'--user={DB_CONFIG["user"]}',
            f'--password={DB_CONFIG["password"]}',
            '--single-transaction',
            '--routines',
            '--triggers',
            '--events',
            '--add-drop-database',
            '--databases',
            DB_CONFIG['database']
        ]
        
        print(f"Starting backup of database: {DB_CONFIG['database']}")
        print(f"Backup file: {backup_file}")
        
        # Execute mysqldump and write to file
        with open(backup_file, 'w', encoding='utf-8') as f:
            process = subprocess.Popen(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"mysqldump failed: {stderr}")
        
        # Get file size
        file_size = os.path.getsize(backup_file)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"Backup completed successfully!")
        print(f"File size: {file_size_mb:.2f} MB")
        print(f"Location: {backup_file}")
        
        # Cleanup old backups
        cleanup_old_backups()
        
        return True, backup_file
        
    except FileNotFoundError:
        error_msg = "mysqldump command not found. Please ensure MySQL client is installed and in PATH."
        print(f"ERROR: {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Backup failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        return False, error_msg

def restore_database(backup_file):
    """Restore database from backup file"""
    try:
        if not os.path.exists(backup_file):
            raise FileNotFoundError(f"Backup file not found: {backup_file}")
        
        print(f"Starting database restore from: {backup_file}")
        print("WARNING: This will replace all current data!")
        
        # Build mysql command
        cmd = [
            'mysql',
            f'--host={DB_CONFIG["host"]}',
            f'--port={DB_CONFIG["port"]}',
            f'--user={DB_CONFIG["user"]}',
            f'--password={DB_CONFIG["password"]}'
        ]
        
        # Execute mysql with backup file as input
        with open(backup_file, 'r', encoding='utf-8') as f:
            process = subprocess.Popen(
                cmd,
                stdin=f,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"mysql restore failed: {stderr}")
        
        print("Database restored successfully!")
        return True, "Restore completed"
        
    except FileNotFoundError as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Restore failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        return False, error_msg

def list_backups():
    """List all available backups"""
    try:
        if not os.path.exists(BACKUP_DIR):
            print("No backups directory found")
            return []
        
        backup_files = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('eyecare_backup_') and filename.endswith('.sql'):
                filepath = os.path.join(BACKUP_DIR, filename)
                size = os.path.getsize(filepath) / (1024 * 1024)  # MB
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                backup_files.append({
                    'filename': filename,
                    'filepath': filepath,
                    'size_mb': f"{size:.2f}",
                    'created': mtime.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by creation time (newest first)
        backup_files.sort(key=lambda x: x['created'], reverse=True)
        
        return backup_files
        
    except Exception as e:
        print(f"Error listing backups: {e}")
        return []

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'backup':
            success, result = backup_database()
            sys.exit(0 if success else 1)
            
        elif command == 'restore':
            if len(sys.argv) < 3:
                print("Usage: python backup_database.py restore <backup_file>")
                sys.exit(1)
            backup_file = sys.argv[2]
            success, result = restore_database(backup_file)
            sys.exit(0 if success else 1)
            
        elif command == 'list':
            backups = list_backups()
            if backups:
                print(f"\nAvailable backups ({len(backups)}):")
                print("-" * 80)
                for backup in backups:
                    print(f"{backup['filename']:<35} {backup['size_mb']:>8} MB  {backup['created']}")
            else:
                print("No backups found")
            sys.exit(0)
            
        else:
            print(f"Unknown command: {command}")
            print("Usage: python backup_database.py [backup|restore|list]")
            sys.exit(1)
    else:
        # Default action: backup
        success, result = backup_database()
        sys.exit(0 if success else 1)
