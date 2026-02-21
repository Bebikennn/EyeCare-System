"""
Automated File Cleanup Script
Safely removes duplicate, obsolete, and one-time use files
Generated: December 26, 2025
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

# Color codes for Windows terminal
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def get_file_size(path):
    """Get file or folder size in bytes"""
    if os.path.isfile(path):
        return os.path.getsize(path)
    elif os.path.isdir(path):
        total = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
        return total
    return 0

def format_size(bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def safe_delete(path, dry_run=True):
    """Safely delete file or folder"""
    try:
        if not os.path.exists(path):
            print_warning(f"Already deleted: {path}")
            return 0
        
        size = get_file_size(path)
        
        if dry_run:
            if os.path.isdir(path):
                print_success(f"Would delete folder: {path} ({format_size(size)})")
            else:
                print_success(f"Would delete file: {path} ({format_size(size)})")
            return size
        else:
            if os.path.isdir(path):
                shutil.rmtree(path)
                print_success(f"Deleted folder: {path} ({format_size(size)})")
            else:
                os.remove(path)
                print_success(f"Deleted file: {path} ({format_size(size)})")
            return size
    except Exception as e:
        print_error(f"Failed to delete {path}: {e}")
        return 0

def main():
    """Main cleanup function"""
    print_header("🗂️  EyeCare Admin - File Cleanup Script")
    
    # Get script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"Working directory: {os.getcwd()}\n")
    
    # Ask for confirmation
    print(f"{Colors.YELLOW}This script will DELETE 49 files and folders.{Colors.RESET}")
    print(f"{Colors.YELLOW}A dry-run will be performed first to show what would be deleted.{Colors.RESET}\n")
    
    # Files to delete (organized by category)
    files_to_delete = {
        "Duplicate Database Files": [
            "database_single.py",
            "database_old.py",
            "config_unified.py"
        ],
        "Old SQL Dumps": [
            "eyecare_db (2).sql",
            "eyecare_merged_database.sql"
        ],
        "Duplicate Documentation": [
            "QUICK_START.md",
            "README_PHASE5A.md",
            "PHASE5A_PROGRESS.md",
            "PHASE5_PLAN.md",
            "PHASE1_COMPLETE.md",
            "PHASE2_COMPLETE.md",
            "PHASE3_COMPLETE.md",
            "PHASE4_COMPLETE.md",
            "ADMIN_WEBSITE_STATUS.md",
            "LOGIN_FIX.md",
            "DATABASE_REAL_DATA.md",
            "IMPLEMENTATION_ROADMAP.md"
        ],
        "Old Test Reports": [
            "system_test_report_20251226_100511.json",
            "system_test_report_20251226_100929.json",
            "test_output.txt"
        ],
        "One-Time Setup Scripts": [
            "add_database_indexes.py",
            "apply_migration.py",
            "run_migration.py",
            "run_migration_eyecare.py",
            "fix_admin_roles.py",
            "fix_missing_columns.py",
            "update_db.py",
            "verify_columns.py",
            "create_test_admins.py",
            "create_test_request.py",
            "check_notifications.py",
            "check_user.py",
            "list_admins.py"
        ],
        "Archived Files": [
            "trashbin"
        ],
        "Python Cache": [
            "__pycache__",
            ".pytest_cache",
            "htmlcov",
            "coverage.xml",
            ".coverage"
        ]
    }
    
    # DRY RUN
    print_header("📋 DRY RUN - Showing what would be deleted")
    
    total_size = 0
    total_files = 0
    
    for category, files in files_to_delete.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.RESET}")
        for file in files:
            size = safe_delete(file, dry_run=True)
            total_size += size
            if size > 0:
                total_files += 1
    
    print(f"\n{Colors.BOLD}Total: {total_files} items, {format_size(total_size)} to reclaim{Colors.RESET}")
    
    # Ask for confirmation to proceed
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
    response = input(f"{Colors.YELLOW}Do you want to proceed with deletion? (yes/no): {Colors.RESET}").strip().lower()
    
    if response not in ['yes', 'y']:
        print_warning("\n❌ Cleanup cancelled by user")
        return
    
    # ACTUAL DELETION
    print_header("🗑️  DELETING FILES")
    
    deleted_size = 0
    deleted_count = 0
    
    for category, files in files_to_delete.items():
        print(f"\n{Colors.BOLD}{category}:{Colors.RESET}")
        for file in files:
            size = safe_delete(file, dry_run=False)
            deleted_size += size
            if size > 0:
                deleted_count += 1
    
    # Summary
    print_header("✅ CLEANUP COMPLETE")
    print(f"{Colors.GREEN}Files deleted: {deleted_count}{Colors.RESET}")
    print(f"{Colors.GREEN}Space reclaimed: {format_size(deleted_size)}{Colors.RESET}")
    
    # Verification recommendation
    print(f"\n{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.YELLOW}NEXT STEPS:{Colors.RESET}")
    print(f"1. Run system test: {Colors.BOLD}python test_full_system.py{Colors.RESET}")
    print(f"2. Verify imports: {Colors.BOLD}python -c \"from app import app; from database import db; print('OK')\"{Colors.RESET}")
    print(f"3. Expected result: System test still at 95.5%")
    print(f"{Colors.YELLOW}{'='*60}{Colors.RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_error("\n\n❌ Cleanup interrupted by user")
    except Exception as e:
        print_error(f"\n\n❌ Unexpected error: {e}")
