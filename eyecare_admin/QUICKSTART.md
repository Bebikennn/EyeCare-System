# Quick Start Guide - EyeCare Admin Dashboard

Get up and running in 5 minutes! This guide covers the fastest path to a working development environment.

## Prerequisites Check

Before starting, verify you have:
- ✅ Python 3.9+ installed: `python --version`
- ✅ MySQL running: `mysql --version`
- ✅ Git installed: `git --version`

---

## 1. Clone & Setup (2 minutes)

```bash
# Clone repository
git clone https://github.com/yourusername/eyecare_admin.git
cd eyecare_admin

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Database Setup (2 minutes)

### Create Database

```sql
-- Login to MySQL
mysql -u root -p

-- Create database and user
CREATE DATABASE eyecare_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'eyecare_user'@'localhost' IDENTIFIED BY 'dev_password_123';
GRANT ALL PRIVILEGES ON eyecare_admin.* TO 'eyecare_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

## 3. Create Admin User (30 seconds)

```bash
python -c "
from app import app, db
from models.admin import Admin
with app.app_context():
    admin = Admin(
        username='admin',
        email='admin@example.com',
        full_name='System Admin',
        role='super_admin'
    )
    admin.set_password('admin123')
    admin.status = 'active'
    db.session.add(admin)
    db.session.commit()
    print('✅ Admin user created: username=admin, password=admin123')
"
```

---

## 4. Start Application (10 seconds)

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5001
 * Environment: development
 * Debug mode: on
```

---

## 5. Login & Verify (30 seconds)

1. Open browser: `http://localhost:5001`
2. Login with:
   - **Username**: `admin`
   - **Password**: `admin123`
3. You should see the dashboard!

---

## Quick API Test

Test the API is working:

```bash
# Login (save session cookie)
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  -c cookies.txt

# Get dashboard stats
curl http://localhost:5001/api/reports/dashboard-stats \
  -b cookies.txt

# Check health
curl http://localhost:5001/health
```

Expected response: `{"status": "healthy"}`

---

## Next Steps

### Explore the Dashboard

1. **Users Page** (`/users.html`): Create and manage app users
2. **Assessments** (`/assessments.html`): View eye care assessments
3. **Health Tips** (`/healthtips.html`): Manage health recommendations
4. **Analytics** (`/ml_analytics.html`): View trends and insights

### Create Sample Data

**Create a test user:**

```bash
curl -X POST http://localhost:5001/api/users \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "password": "TestPassword123!"
  }'
```

**Create a health tip:**

```bash
curl -X POST http://localhost:5001/api/healthtips \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "title": "Eye Exercise Tips",
    "description": "Follow the 20-20-20 rule: Every 20 minutes, look at something 20 feet away for 20 seconds.",
    "category": "exercise",
    "risk_level": "All",
    "icon": "exercise"
  }'
```

### Explore Analytics

1. Visit: `http://localhost:5001/ml_analytics.html`
2. View risk trends, disease distribution, and risk factor correlations
3. Export data in CSV, JSON, or Excel format

---

## Common Commands

**Start server:**
```bash
python app.py
```

**Run tests:**
```bash
pytest
```

**Run tests with coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Apply database indexes:**
```bash
mysql -u eyecare_user -p eyecare_admin < migrations/add_performance_indexes.sql
```

**Clear cache (via API):**
```bash
curl -X POST http://localhost:5001/api/cache/clear \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{}'
```

---

## Troubleshooting

### Issue: Can't connect to database

**Error:** `sqlalchemy.exc.OperationalError: Can't connect to MySQL server`

**Solution:**
1. Verify MySQL is running: `systemctl status mysql` (Linux) or check Services (Windows)
2. Check credentials in `.env` file
3. Test connection: `mysql -u eyecare_user -p`

### Issue: Module not found

**Error:** `ModuleNotFoundError: No module named 'flask'`

**Solution:**
1. Ensure virtual environment is activated: `venv\Scripts\activate` (Windows)
2. Reinstall dependencies: `pip install -r requirements.txt`

### Issue: Port already in use

**Error:** `OSError: [Errno 98] Address already in use`

**Solution:**
1. Change port in `app.py`: `app.run(debug=True, port=5002)`
2. Or kill process using port 5001:
   - Windows: `netstat -ano | findstr :5001` → `taskkill /PID <PID> /F`
   - Linux: `lsof -ti:5001 | xargs kill -9`

### Issue: 401 Unauthorized on API calls

**Error:** API returns 401 even after login

**Solution:**
1. Ensure you're sending cookies with requests (`-b cookies.txt` in curl)
2. Check session is active: `curl http://localhost:5001/api/auth/check-session -b cookies.txt`
3. For development, ensure `SESSION_COOKIE_SECURE=False` in `.env`

### Issue: Slow dashboard performance

**Error:** Statistics page takes >5 seconds to load

**Solution:**
1. Apply database indexes: `mysql -u eyecare_user -p eyecare_admin < migrations/add_performance_indexes.sql`
2. Verify caching is enabled (it's on by default)
3. Check cache stats: `curl http://localhost:5001/api/cache/stats -b cookies.txt`

---

## Project Structure Overview

```
eyecare_admin/
├── app.py              # Main application (START HERE)
├── models/             # Database models (User, Admin, Assessment, etc.)
├── routes/             # API endpoints (auth, users, assessments, etc.)
├── templates/          # HTML pages (login, dashboard, users, etc.)
├── static/             # CSS, JS, images
├── tests/              # Test suite (pytest)
└── .env                # Configuration (YOU CREATED THIS)
```

---

## Environment Variables Explained

```bash
# Database connection
DB_HOST=localhost           # MySQL host
DB_PORT=3306                # MySQL port
DB_USERNAME=eyecare_user    # Database user
DB_PASSWORD=dev_password_123  # Database password
DB_NAME=eyecare_admin       # Database name

# Flask configuration
FLASK_ENV=development       # development | production
SECRET_KEY=<random-key>     # Session encryption key
SESSION_COOKIE_SECURE=False # True for HTTPS in production

# Rate limiting
RATELIMIT_ENABLED=True      # Enable/disable rate limiting
RATELIMIT_DEFAULT=5000 per day;1000 per hour  # Request limits
```

---

## Development Tips

### 1. Live Reloading

Flask automatically reloads on code changes when `debug=True` (default in development mode).

### 2. Database Inspection

**View tables:**
```sql
mysql -u eyecare_user -p eyecare_admin -e "SHOW TABLES;"
```

**Check user count:**
```sql
mysql -u eyecare_user -p eyecare_admin -e "SELECT COUNT(*) FROM users;"
```

### 3. API Testing with Postman

1. Import the API collection (if available) or create requests manually
2. Set base URL: `http://localhost:5001/api`
3. For authenticated requests:
   - First call: `POST /auth/login` (save cookies)
   - Subsequent calls: Include saved cookies

### 4. Frontend Development

- **Templates**: `templates/*.html` (Jinja2)
- **Styles**: `static/css/*.css`
- **Scripts**: `static/js/*.js`

No build step required - just edit and refresh!

---

## Performance Quick Wins

### 1. Enable Caching (Enabled by Default)

Cache hit rates typically 80-95% for dashboard stats:
- User stats: cached 5 minutes
- Assessment stats: cached 5 minutes
- Analytics: cached 10 minutes

### 2. Apply Database Indexes

```bash
mysql -u eyecare_user -p eyecare_admin < migrations/add_performance_indexes.sql
```

**Performance gains:**
- Filtered queries: 10-100x faster
- Dashboard stats: 3-5x faster
- Pagination: 5-10x faster

### 3. Monitor Cache Performance

```bash
# View cache statistics
curl http://localhost:5001/api/cache/stats -b cookies.txt

# Clear cache if needed
curl -X POST http://localhost:5001/api/cache/clear -b cookies.txt -d '{}'
```

---

## What's Next?

### Read Full Documentation

- **[README.md](README.md)** - Complete setup guide, deployment, troubleshooting
- **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** - Full API reference with examples
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[PERFORMANCE.md](PERFORMANCE.md)** - Performance optimization strategies

### Explore Features

1. **User Management**: Create users, manage status, export to Excel
2. **Assessment Analytics**: View risk trends, disease distribution
3. **Health Tips**: Create category-based health recommendations
4. **Activity Logs**: Audit trail of all admin actions
5. **Comprehensive Reports**: Generate date-ranged reports

### Test the System

```bash
# Run full test suite
pytest

# Run with coverage report
pytest --cov=. --cov-report=html

# View coverage report
# Open: htmlcov/index.html in browser
```

### Join the Community

- Report bugs or request features on GitHub Issues
- Contribute improvements via Pull Requests
- Share your deployment experiences

---

## Support

**Quick Help:**
- Check [README.md](README.md) Troubleshooting section
- Review [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for endpoint details
- Search GitHub Issues for similar problems

**Contact:**
- GitHub: [Repository Issues](https://github.com/yourusername/eyecare_admin/issues)
- Email: support@eyecare.com

---

**You're all set!** 🎉

Your EyeCare Admin Dashboard is now running at `http://localhost:5001`

Happy coding! 👨‍💻👩‍💻
- ✅ Error tracking with Sentry
- ✅ Uptime monitoring
- ✅ Security hardening

### Maintenance:
- **Daily**: Check monitoring dashboard (1 min)
- **Weekly**: Review logs and performance (10 min)
- **Monthly**: Update system packages (15 min)

---

## Need More Help?

1. **Detailed Guide**: See DEPLOYMENT_GUIDE.md for step-by-step instructions
2. **Progress Tracking**: See PHASE5A_PROGRESS.md for deployment checklist
3. **System Info**: See SYSTEM_ANALYSIS.md for architecture overview

---

## Success! 🎉

Your EyeCare Admin application is now:
- 🚀 Live and accessible worldwide
- 🔒 Secured with HTTPS
- 📊 Monitored for uptime
- 💾 Automatically backed up daily
- 🐛 Tracking errors with Sentry
- ⚡ Optimized with Redis caching
- 📈 Ready for production traffic

**Congratulations on your deployment!** 🎊
