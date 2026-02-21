# EyeCare App - Quick Action Plan

## 🎯 Current Status
**Overall Completion: 85-90%**
- ✅ Core features working
- ⚠️ Production readiness: 40%
- ⚠️ Security: Needs hardening
- ⚠️ Testing: Minimal coverage

---

## 🔴 CRITICAL (Do This First - 12-16 hours)

### 1. Security Hardening (4 hours)

**File: eyecare_backend/app.py**
```python
# CHANGE THIS LINE:
app.run(host="0.0.0.0", port=5000, debug=True)

# TO:
app.run(host="0.0.0.0", port=5000, debug=False)
```

**Create: eyecare_backend/.env**
```env
# Database
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=eyecare_db

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password

# Security
SECRET_KEY=your_super_secret_key_here
JWT_SECRET_KEY=another_secret_key
```

**Update: eyecare_backend/config.py**
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'eyecare_db')

# Email Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
```

**Add Rate Limiting:**
```bash
pip install Flask-Limiter
```

```python
# In app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to login endpoint
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    # existing code
```

---

### 2. Production Server Setup (4 hours)

**Install Gunicorn:**
```bash
pip install gunicorn
```

**Create: eyecare_backend/gunicorn_config.py**
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"
```

**Run with Gunicorn:**
```bash
gunicorn -c gunicorn_config.py app:app
```

**Create Nginx config (optional):**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

### 3. Error Handling & Logging (2 hours)

**Update: eyecare_backend/app.py**
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler(
    'logs/eyecare.log',
    maxBytes=10240000,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# Global error handlers
@app.errorhandler(404)
def not_found(error):
    app.logger.error(f"404 error: {request.url}")
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {error}")
    return jsonify({"error": "Internal server error"}), 500
```

**Add to each route:**
```python
try:
    # existing code
except Exception as e:
    app.logger.error(f"Error in endpoint: {str(e)}")
    return jsonify({"error": str(e)}), 500
```

---

### 4. Basic Testing (6 hours)

**Create: eyecare_backend/tests/test_auth.py**
```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login_success(client):
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpass123'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'

def test_login_invalid(client):
    response = client.post('/login', json={
        'username': 'invalid',
        'password': 'wrong'
    })
    assert response.status_code == 401

def test_register(client):
    response = client.post('/register', json={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'pass123'
    })
    assert response.status_code in [200, 201]
```

**Run tests:**
```bash
pip install pytest pytest-cov
pytest tests/ -v
```

---

## 🟡 HIGH PRIORITY (Next 16-20 hours)

### 5. API Documentation (4 hours)

**Install Flasgger:**
```bash
pip install flasgger
```

**Update app.py:**
```python
from flasgger import Swagger

swagger = Swagger(app, template={
    "info": {
        "title": "EyeCare API",
        "description": "Eye Disease Risk Assessment API",
        "version": "1.0.0"
    }
})
```

**Add to routes:**
```python
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    User Login
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    # existing code
```

**Access docs at:** http://localhost:5000/apidocs

---

### 6. Performance Optimization (6 hours)

**Add Redis Caching:**
```bash
pip install redis Flask-Caching
```

```python
from flask_caching import Cache

cache = Cache(app, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@assessment_bp.route("/api/assessment/history/<user_id>", methods=["GET"])
@cache.cached(timeout=300, key_prefix='history')
def get_assessment_history(user_id):
    # existing code
```

**Database Connection Pooling:**
```python
# Update services/db.py
from sqlalchemy import create_engine, pool

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}",
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20
)
```

**Optimize ML Model Loading:**
```python
# In ml_predict.py, already done with _model_cache ✓
```

---

### 7. Mobile App Polish (6 hours)

**Add Connectivity Check:**
```yaml
# pubspec.yaml
dependencies:
  connectivity_plus: ^5.0.0
```

```dart
// lib/services/connectivity_service.dart
import 'package:connectivity_plus/connectivity_plus.dart';

class ConnectivityService {
  Future<bool> hasConnection() async {
    var result = await Connectivity().checkConnectivity();
    return result != ConnectivityResult.none;
  }
}
```

**Add Loading Skeletons:**
```yaml
dependencies:
  shimmer: ^3.0.0
```

**Add Pull-to-Refresh:**
```dart
RefreshIndicator(
  onRefresh: () async {
    await loadData();
  },
  child: ListView(...)
)
```

**Better Error Messages:**
```dart
void showError(String message) {
  ScaffoldMessenger.of(context).showSnackBar(
    SnackBar(
      content: Text(message),
      backgroundColor: Colors.red,
      action: SnackBarAction(
        label: 'Retry',
        textColor: Colors.white,
        onPressed: () => retry(),
      ),
    ),
  );
}
```

---

### 8. Monitoring Setup (4 hours)

**Install Sentry:**
```bash
pip install sentry-sdk[flask]
```

```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

**Firebase Analytics (Flutter):**
```yaml
dependencies:
  firebase_core: ^2.24.0
  firebase_analytics: ^10.7.0
```

```dart
import 'package:firebase_analytics/firebase_analytics.dart';

FirebaseAnalytics analytics = FirebaseAnalytics.instance;
analytics.logEvent(name: 'assessment_completed');
```

---

## 🟢 MEDIUM PRIORITY (20-24 hours)

### 9. Push Notifications (6 hours)

**Backend - Firebase Admin:**
```bash
pip install firebase-admin
```

```python
import firebase_admin
from firebase_admin import messaging

def send_push_notification(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token
    )
    response = messaging.send(message)
    return response
```

**Flutter:**
```yaml
dependencies:
  firebase_messaging: ^14.7.0
```

---

### 10. Advanced Features (8 hours)
- Dark mode
- Multi-language
- Accessibility

### 11. Admin Integration (6 hours)
- User management API
- Analytics dashboard

### 12. Comprehensive Docs (4 hours)
- User manual
- Video tutorials

---

## 📋 Checklist Format

### Security Hardening:
- [ ] Remove debug mode
- [ ] Create .env file
- [ ] Update config.py
- [ ] Add rate limiting
- [ ] Implement JWT auth
- [ ] Add input validation

### Production Setup:
- [ ] Install Gunicorn
- [ ] Create gunicorn_config.py
- [ ] Test Gunicorn startup
- [ ] Configure Nginx (optional)
- [ ] Set up SSL certificates
- [ ] Configure domain name

### Error Handling:
- [ ] Add logging configuration
- [ ] Create logs directory
- [ ] Add global error handlers
- [ ] Update all routes with try-catch
- [ ] Test error scenarios

### Testing:
- [ ] Create tests directory
- [ ] Write auth tests
- [ ] Write assessment tests
- [ ] Write ML prediction tests
- [ ] Run test suite
- [ ] Check coverage (target: 70%+)

### API Documentation:
- [ ] Install Flasgger
- [ ] Add Swagger config
- [ ] Document all endpoints
- [ ] Test documentation UI
- [ ] Export Postman collection

### Performance:
- [ ] Install Redis
- [ ] Add caching to endpoints
- [ ] Implement connection pooling
- [ ] Optimize database queries
- [ ] Compress API responses

### Mobile Polish:
- [ ] Add connectivity check
- [ ] Implement loading skeletons
- [ ] Add pull-to-refresh
- [ ] Improve error messages
- [ ] Add offline mode

### Monitoring:
- [ ] Set up Sentry
- [ ] Add Firebase Analytics
- [ ] Configure log rotation
- [ ] Set up health checks
- [ ] Create monitoring dashboard

---

## 🚀 Quick Start Commands

### Backend Setup:
```bash
cd eyecare_backend

# Install dependencies
pip install -r requirements.txt
pip install gunicorn Flask-Limiter python-dotenv pytest flasgger redis Flask-Caching sentry-sdk

# Create environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
pytest tests/ -v

# Run with Gunicorn
gunicorn -c gunicorn_config.py app:app
```

### Flutter Setup:
```bash
cd ../

# Get dependencies
flutter pub get

# Run on emulator
flutter run

# Build APK
flutter build apk --release
```

---

## 📊 Progress Tracking

Create a simple tracking sheet:

| Task | Priority | Hours | Status | Notes |
|------|----------|-------|--------|-------|
| Remove debug mode | Critical | 0.5 | ⬜ | |
| Create .env | Critical | 1 | ⬜ | |
| Add rate limiting | Critical | 2 | ⬜ | |
| Setup Gunicorn | Critical | 2 | ⬜ | |
| Add logging | Critical | 2 | ⬜ | |
| Write tests | Critical | 6 | ⬜ | |
| API docs | High | 4 | ⬜ | |
| Add caching | High | 4 | ⬜ | |
| Mobile polish | High | 6 | ⬜ | |
| Monitoring | High | 4 | ⬜ | |

**Total Critical Hours:** 13.5  
**Total High Priority Hours:** 18

---

## 💡 Pro Tips

1. **Start with security** - Don't skip this!
2. **Test as you go** - Don't wait until the end
3. **Document while fresh** - Code is easier to document right after writing
4. **Monitor early** - Catch issues before users do
5. **Backup database** - Before any major changes

---

## 📞 Need Help?

### Common Issues:

**"Backend won't start"**
- Check XAMPP MySQL is running
- Verify database credentials in .env
- Check if port 5000 is available

**"Flutter can't connect"**
- Update baseUrl in lib/services/api.dart
- Check backend is running
- Verify firewall settings

**"ML model not found"**
- Model exists at: eyecare_backend/models/lightgbm_model.pkl
- Check file permissions
- Re-train if necessary

---

## ✅ Ready to Deploy When:

- [ ] All critical tasks complete
- [ ] Tests passing (70%+ coverage)
- [ ] Security audit passed
- [ ] Performance tested (100+ users)
- [ ] Documentation complete
- [ ] Monitoring active
- [ ] Backup strategy in place
- [ ] Rollback plan ready

---

**Created:** January 2, 2026  
**Last Updated:** January 2, 2026  
**Version:** 1.0

**Use this as your roadmap to production!** 🚀
