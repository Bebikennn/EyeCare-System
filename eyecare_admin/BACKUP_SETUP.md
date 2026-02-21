# Database Backup Setup Instructions

## Overview
The database backup system creates automatic backups of your MySQL database and manages retention.

## Features
- **Automated backups** using mysqldump
- **Retention policy**: Keeps last 30 backups automatically
- **Consistent backups**: Uses --single-transaction for InnoDB tables
- **Easy restore**: Simple command-line restore functionality
- **Backup listing**: View all available backups with details

## Manual Backup

### Run Backup Now
```bash
python scripts\backup_database.py backup
```

Or simply use the batch file:
```bash
BACKUP_DATABASE.bat
```

### List All Backups
```bash
python scripts\backup_database.py list
```

### Restore from Backup
```bash
python scripts\backup_database.py restore backups\eyecare_backup_20240101_120000.sql
```

## Automated Backup Setup (Windows Task Scheduler)

### Step 1: Open Task Scheduler
1. Press `Win + R`
2. Type `taskschd.msc` and press Enter

### Step 2: Create New Task
1. Click "Create Task" (not "Create Basic Task")
2. Name: `EyeCare Database Backup`
3. Description: `Daily backup of EyeCare database`
4. Check "Run whether user is logged on or not"
5. Check "Run with highest privileges"

### Step 3: Configure Trigger
1. Go to "Triggers" tab
2. Click "New..."
3. Set:
   - Begin the task: **On a schedule**
   - Settings: **Daily**
   - Start: Choose time (e.g., **2:00 AM**)
   - Recur every: **1 days**
   - Enabled: **Checked**
4. Click "OK"

### Step 4: Configure Action
1. Go to "Actions" tab
2. Click "New..."
3. Set:
   - Action: **Start a program**
   - Program/script: `D:\Users\johnv\Projects\eyecare_admin\BACKUP_DATABASE.bat`
   - Start in: `D:\Users\johnv\Projects\eyecare_admin`
4. Click "OK"

### Step 5: Configure Settings
1. Go to "Settings" tab
2. Check:
   - ✅ Allow task to be run on demand
   - ✅ Run task as soon as possible after a scheduled start is missed
   - ✅ If the task fails, restart every: **10 minutes** (Attempt 3 times)
3. Uncheck:
   - ❌ Stop the task if it runs longer than: 3 days
4. Click "OK"

### Step 6: Save and Test
1. Click "OK" to save the task
2. Enter your Windows password if prompted
3. Right-click the task and select "Run" to test it immediately

## Backup Location
Backups are stored in: `D:\Users\johnv\Projects\eyecare_admin\backups\`

## Backup File Format
`eyecare_backup_YYYYMMDD_HHMMSS.sql`

Example: `eyecare_backup_20240315_020000.sql`

## Backup Logs
Check backup execution logs in: `logs\backup.log`

## Retention Policy
- **Automatic cleanup**: Keeps last 30 backups
- Older backups are automatically deleted
- Adjust `MAX_BACKUPS` in `scripts/backup_database.py` to change retention

## Prerequisites
- MySQL client tools must be installed (mysqldump and mysql commands)
- MySQL client must be in system PATH
- Virtual environment must be set up

## Troubleshooting

### mysqldump not found
**Solution**: Add MySQL bin directory to PATH
1. Locate MySQL installation (e.g., `C:\Program Files\MySQL\MySQL Server 8.0\bin`)
2. Add to System Environment Variables > PATH
3. Restart command prompt/Task Scheduler

### Backup fails with access denied
**Solution**: Check database credentials in `.env` file
```
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=eyecare_db
```

### Task runs but no backup created
**Solution**: Check logs
1. Review `logs\backup.log` for error messages
2. Run `BACKUP_DATABASE.bat` manually to see errors
3. Verify virtual environment is activated

### Restore overwrites data
**Warning**: Restore completely replaces current database
- Always backup current data before restoring
- Use with caution in production

## Best Practices
1. **Test restores regularly** to ensure backups are valid
2. **Keep offsite copies** of critical backups
3. **Monitor backup logs** for failures
4. **Schedule during low-usage hours** (e.g., 2 AM)
5. **Verify backup files** after creation

## Manual Verification
After each backup, verify the file:
```bash
# Check backup file exists and has content
dir backups

# View backup file size
python scripts\backup_database.py list
```
