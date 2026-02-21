# EyeCare Admin Dashboard

A comprehensive Flask-based administrative dashboard for managing eye care assessments, users, health tips, and analytics. Built with modern web technologies and optimized for performance.

## Features

### Core Functionality
- **User Management**: CRUD operations, status management (active/blocked/archived), bulk export
- **Assessment Tracking**: Risk level analysis (Low/Moderate/High), disease prediction monitoring
- **Health Tips**: Category-based tips (diet, exercise, lifestyle), risk-level targeting
- **Activity Logging**: Comprehensive audit trail of admin actions
- **Analytics Dashboard**: Real-time statistics, trends, and insights

### Advanced Features
- **Multi-format Export**: CSV, JSON, Excel support for users and assessments
- **Analytics API**: Risk level trends, disease distribution, risk factor correlation
- **Comprehensive Reports**: Date-range filtered reports with daily breakdown
- **Performance Optimization**: Query result caching (5-10min TTL), database indexing
- **Security**: Session management, CSRF protection, rate limiting, role-based access

### Technical Highlights
- **Flask 3.1.2** with Blueprint architecture for modular routing
- **SQLAlchemy 2.0** ORM with MySQL backend
- **In-memory caching** with smart invalidation patterns
- **Pytest** test suite with 67+ passing tests
- **Production-ready** deployment with gunicorn + nginx

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Performance](#performance)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** (3.10+ recommended)
- **MySQL 5.7+** or **MariaDB 10.3+**
- **pip** (Python package manager)
- **virtualenv** (recommended for isolation)
- **Git** (for cloning the repository)

### Optional
- **Redis** (for distributed caching in production - future enhancement)
- **Node.js** (if you need to modify frontend assets)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/eyecare_admin.git
cd eyecare_admin
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- Flask 3.1.2
- SQLAlchemy 2.0.44
- Flask-SQLAlchemy 3.1.1
- pymysql 1.1.1
- Flask-Limiter 3.9.3
- pytest 8.3.5
- gunicorn 21.2.0
- openpyxl 3.1.5

---

## Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your settings:

```bash
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here-change-in-production
SESSION_COOKIE_NAME=eyecare_admin_session

# Database Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=eyecare_user
DB_PASSWORD=your-db-password
DB_NAME=eyecare_admin

# Security
CSRF_ENABLED=True
SESSION_COOKIE_SECURE=False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_DEFAULT=1000 per day;100 per hour

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### 3. Generate Secret Key

**Windows (PowerShell):**
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

**Linux/macOS:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

---

## Database Setup

### 1. Create MySQL Database

```sql
CREATE DATABASE eyecare_admin CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'eyecare_user'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON eyecare_admin.* TO 'eyecare_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Initialize Database Schema

```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### 3. Apply Performance Indexes (Recommended)

```bash
mysql -u eyecare_user -p eyecare_admin < migrations/add_performance_indexes.sql
```

**Performance Impact:**
- 10-100x faster filtered queries
- Improved sorting and pagination
- Better dashboard statistics performance

### 4. Create Default Admin User

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
    admin.set_password('YourSecurePassword123!')
    admin.status = 'active'
    db.session.add(admin)
    db.session.commit()
    print('Admin user created successfully')
"
```

---

## Running the Application

### Development Mode

**Windows:**
```bash
python app.py
```

**Linux/macOS:**
```bash
python3 app.py
```

Access the application at: `http://localhost:5001`

**Default Credentials:**
- Username: `admin`
- Password: (the password you set during admin creation)

### Production Mode

Use the provided batch script or gunicorn directly:

**Windows:**
```bash
START_ADMIN.bat
```

**Linux/macOS:**
```bash
gunicorn -c gunicorn.conf.py wsgi:application
```

For detailed production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## Testing

### Run Test Suite

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=. --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_models.py -v
```

**Test Configuration:**
- Uses in-memory SQLite for speed and isolation
- 67+ passing tests covering models, routes, and services
- Test database automatically created/destroyed

### Test Categories

- **Model Tests**: User, Admin, Assessment, HealthTip models
- **Route Tests**: Authentication, user management, assessments
- **Service Tests**: Email service, export utilities
- **Integration Tests**: End-to-end API workflows

---

## Deployment

### Quick Production Checklist

1. ✅ Set `FLASK_ENV=production` in `.env`
2. ✅ Generate strong `SECRET_KEY`
3. ✅ Set `SESSION_COOKIE_SECURE=True` (requires HTTPS)
4. ✅ Configure production database credentials
5. ✅ Apply database indexes: `add_performance_indexes.sql`
6. ✅ Set up gunicorn with systemd (see DEPLOYMENT.md)
7. ✅ Configure nginx reverse proxy
8. ✅ Enable firewall rules (ports 80, 443)
9. ✅ Set up SSL certificate (Let's Encrypt)
10. ✅ Configure log rotation

### Deployment Scripts

- **Windows**: `START_ADMIN.bat`
- **Linux**: `deployment/systemd/eyecare-admin.service`
- **Nginx**: `deployment/nginx/eyecare-admin.conf`

**Full deployment guide:** [DEPLOYMENT.md](DEPLOYMENT.md)

---

## API Documentation

### Quick API Overview

**Base URL:** `http://localhost:5001/api`

**Authentication:** Session-based (login required for all endpoints except `/auth/login`)

**Key Endpoints:**
- `POST /auth/login` - Authenticate user
- `GET /users` - List users (paginated, filtered)
- `GET /users/stats` - User statistics (cached 5min)
- `GET /assessments` - List assessments (paginated, filtered)
- `GET /assessments/stats` - Assessment statistics (cached 5min)
- `GET /assessments/trends/risk-level` - Risk trends (cached 10min)
- `GET /assessments/analytics/disease-distribution` - Disease stats (cached 10min)
- `GET /assessments/analytics/risk-factors` - Risk factor correlation (cached 10min)
- `GET /reports/comprehensive` - Generate comprehensive reports

**Export Formats:** CSV, JSON, Excel

**Full API reference:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

## Performance

### Caching Strategy

**Query Result Caching:**
- User statistics: 5 minutes TTL
- Assessment statistics: 5 minutes TTL
- Analytics endpoints: 10 minutes TTL
- Dashboard stats: 5 minutes TTL

**Cache Invalidation:**
- Automatic on data modifications (create, update, delete)
- Manual via `/api/cache/clear` endpoint
- Pattern-based invalidation (e.g., `user_stats:*`)

**Performance Gains:**
- 20-100x faster stats endpoints (cached vs uncached)
- 10-100x faster filtered queries (with indexes)

### Database Indexing

Applied indexes for optimal query performance:
- **Users**: status, created_at, composite (status, created_at)
- **Assessments**: risk_level, assessed_at, user_id, composite indexes
- **Health Tips**: category, status
- **Activity Logs**: admin_id, action, created_at
- **Admins**: role, status, last_login

**Full performance guide:** [PERFORMANCE.md](PERFORMANCE.md)

---

## Project Structure

```
eyecare_admin/
├── app.py                      # Main application entry point
├── wsgi.py                     # WSGI server entry point
├── config.py                   # Configuration classes
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
├── gunicorn.conf.py            # Gunicorn configuration
│
├── models/                     # SQLAlchemy models
│   ├── admin.py                # Admin user model
│   ├── user.py                 # App user model
│   ├── assessment.py           # Assessment model
│   ├── health_tip.py           # Health tip model
│   └── activity_log.py         # Activity log model
│
├── routes/                     # Flask blueprints
│   ├── auth.py                 # Authentication routes
│   ├── users.py                # User management
│   ├── assessments.py          # Assessment management + analytics
│   ├── healthtips.py           # Health tips management
│   ├── admin_routes.py         # Admin management
│   ├── logs.py                 # Activity logs
│   └── ml_routes.py            # ML model routes
│
├── services/                   # Business logic
│   ├── email_service.py        # Email notifications
│   └── ...
│
├── utils/                      # Utility modules
│   ├── cache.py                # Caching utilities
│   ├── export.py               # Export utilities (CSV/Excel/JSON)
│   └── decorators.py           # Custom decorators
│
├── migrations/                 # Database migrations
│   └── add_performance_indexes.sql
│
├── deployment/                 # Deployment configs
│   ├── systemd/                # systemd service files
│   └── nginx/                  # nginx configurations
│
├── tests/                      # Test suite
│   ├── conftest.py             # pytest fixtures
│   ├── test_models.py          # Model tests
│   ├── test_routes.py          # Route tests
│   └── ...
│
├── static/                     # Frontend assets
│   ├── css/                    # Stylesheets
│   ├── js/                     # JavaScript
│   └── images/                 # Images
│
├── templates/                  # Jinja2 templates
│   ├── admin.html              # Admin management
│   ├── users.html              # User management
│   ├── assessments.html        # Assessment dashboard
│   ├── ml_analytics.html       # ML analytics
│   └── ...
│
└── instance/                   # Instance-specific files (gitignored)
    └── eyecare_admin.db        # SQLite database (development)
```

---

## Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Code Standards

- Follow PEP 8 style guide
- Write descriptive commit messages
- Add tests for new features
- Update documentation as needed
- Run `pytest` before submitting PR

### Testing Checklist

- [ ] All tests pass: `pytest`
- [ ] Code coverage > 80%: `pytest --cov`
- [ ] No linting errors
- [ ] Documentation updated

---

## Troubleshooting

### Common Issues

**1. Database Connection Error**
```
Error: Can't connect to MySQL server
```
**Solution:** Check MySQL is running, verify credentials in `.env`

**2. Import Error for Models**
```
ModuleNotFoundError: No module named 'models'
```
**Solution:** Ensure virtual environment is activated, reinstall dependencies

**3. Session Cookie Not Working**
```
401 Unauthorized on authenticated endpoints
```
**Solution:** Check `SESSION_COOKIE_SECURE` setting (should be False for HTTP)

**4. Port Already in Use**
```
OSError: [Errno 98] Address already in use
```
**Solution:** Change port in `app.py` or kill process using port 5001

**5. Performance Issues**
```
Slow query response times
```
**Solution:** Apply database indexes: `migrations/add_performance_indexes.sql`

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For issues, questions, or contributions:

- **GitHub Issues**: [Repository Issues](https://github.com/yourusername/eyecare_admin/issues)
- **Email**: support@eyecare.com
- **Documentation**: See `/docs` folder for additional guides

---

## Acknowledgments

- Flask framework and ecosystem
- SQLAlchemy ORM
- Bootstrap UI framework
- Chart.js for analytics visualizations
- All contributors and testers

---

**Version:** 1.0.0  
**Last Updated:** January 1, 2026  
**Status:** Production Ready ✅
