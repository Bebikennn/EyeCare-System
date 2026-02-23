from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import os
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from sqlalchemy.pool import StaticPool

app = Flask(__name__)

_IS_PROD_CONFIG = False
_IS_TESTING = os.getenv('TESTING', '').lower() in ('1', 'true', 'yes') or os.getenv('FLASK_ENV') == 'testing'
_CORS_ORIGINS = None
_RATELIMIT_STORAGE_URI = "memory://"
_RATELIMIT_DEFAULT_LIMITS = ["5000 per day", "1000 per hour"]

# Load configuration (testing, production, or development)
if _IS_TESTING:
    print("Loading testing configuration...")

    # Use an in-memory SQLite DB for tests so we don't touch MySQL.
    # StaticPool keeps a single connection alive across the app lifecycle,
    # which is required for in-memory SQLite to persist across requests.
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False},
        'poolclass': StaticPool,
    }
    SECRET_KEY = 'test-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'static/uploads'
    DEBUG = False
    SESSION_LIFETIME_HOURS = 2
    PREFERRED_URL_SCHEME = 'http'

    # Mail (suppressed in tests by conftest)
    MAIL_SERVER = 'localhost'
    MAIL_PORT = 25
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    MAIL_DEFAULT_SENDER = 'test@example.com'

    MAX_CONTENT_LENGTH = 16777216

elif os.getenv('FLASK_ENV', '').lower() == 'production' or os.getenv('RENDER'):
    print("Loading production configuration...")
    _IS_PROD_CONFIG = True
    from config_production import (
        SQLALCHEMY_DATABASE_URI, 
        SQLALCHEMY_ENGINE_OPTIONS,
        SECRET_KEY,
        SQLALCHEMY_TRACK_MODIFICATIONS,
        UPLOAD_FOLDER,
        DEBUG,
        SESSION_COOKIE_SECURE,
        SESSION_LIFETIME_HOURS,
        PREFERRED_URL_SCHEME,
        MAIL_SERVER,
        MAIL_PORT,
        MAIL_USE_TLS,
        MAIL_USERNAME,
        MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER,
        RATELIMIT_STORAGE_URL,
        RATELIMIT_DEFAULT,
        CORS_ORIGINS,
        MAX_CONTENT_LENGTH
    )
    app.config['SESSION_COOKIE_SECURE'] = SESSION_COOKIE_SECURE
    app.config['PREFERRED_URL_SCHEME'] = PREFERRED_URL_SCHEME

    _RATELIMIT_STORAGE_URI = RATELIMIT_STORAGE_URL
    _RATELIMIT_DEFAULT_LIMITS = [limit.strip() for limit in RATELIMIT_DEFAULT.split(';') if limit.strip()]
    _CORS_ORIGINS = [origin.strip() for origin in (CORS_ORIGINS or '').split(',') if origin.strip()] or None
else:
    print("Loading development configuration...")
    from config import (
        SQLALCHEMY_DATABASE_URI, 
        SQLALCHEMY_ENGINE_OPTIONS,
        SECRET_KEY,
        SQLALCHEMY_TRACK_MODIFICATIONS,
        UPLOAD_FOLDER,
        DEBUG,
        MAIL_SERVER,
        MAIL_PORT,
        MAIL_USE_TLS,
        MAIL_USERNAME,
        MAIL_PASSWORD,
        MAIL_DEFAULT_SENDER,
        MAX_CONTENT_LENGTH
    )
    SESSION_LIFETIME_HOURS = 2

app.config['SECRET_KEY'] = SECRET_KEY
app.config['DEBUG'] = DEBUG
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = SQLALCHEMY_ENGINE_OPTIONS
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Secure Session Configuration
if 'SESSION_COOKIE_SECURE' not in app.config:
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True when using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=SESSION_LIFETIME_HOURS)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# Initialize Sentry for error tracking (production)
if not DEBUG and os.getenv('SENTRY_DSN'):
    try:
        from sentry_integration import init_sentry
        init_sentry(app)
    except Exception as e:
        app.logger.warning(f"Failed to initialize Sentry: {e}")

# Mail Config
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

# Setup logging
if not app.debug:
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # File handler for general logs
    file_handler = RotatingFileHandler(
        'logs/eyecare_admin.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # File handler for errors
    error_handler = RotatingFileHandler(
        'logs/eyecare_admin_errors.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]\n'
        'Traceback:\n%(exc_info)s'
    ))
    error_handler.setLevel(logging.ERROR)
    app.logger.addHandler(error_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('EyeCare Admin startup')

if app.debug:
    CORS(app, supports_credentials=True)
elif _CORS_ORIGINS:
    CORS(app, origins=_CORS_ORIGINS, supports_credentials=True)

# Initialize CSRF Protection
csrf = CSRFProtect(app)

# Initialize Rate Limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=_RATELIMIT_DEFAULT_LIMITS,
    storage_uri=_RATELIMIT_STORAGE_URI
)


@app.after_request
def _add_security_headers(response):
    # Basic security headers (safe defaults). Tune further if you add CSP/nonces.
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')

    # Enforce HTTPS only when we're configured for production.
    if _IS_PROD_CONFIG:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')

    return response

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import database
from database import db, init_db

# Initialize database
db.init_app(app)


def _bootstrap_admin_if_configured() -> None:
    """Create or reset a super-admin account on startup (production only).

    Enable with:
      BOOTSTRAP_ADMIN_ENABLE=true

    Required vars:
      BOOTSTRAP_ADMIN_USERNAME
      BOOTSTRAP_ADMIN_EMAIL
      BOOTSTRAP_ADMIN_FULL_NAME
      BOOTSTRAP_ADMIN_PASSWORD

    Optional vars:
      BOOTSTRAP_ADMIN_ROLE (default: super_admin)
      BOOTSTRAP_ADMIN_STATUS (default: active)
      BOOTSTRAP_ADMIN_FORCE_PASSWORD_CHANGE (default: true)
      BOOTSTRAP_ADMIN_RESET_EXISTING (default: false)
    """

    if not _IS_PROD_CONFIG:
        return

    if os.getenv('BOOTSTRAP_ADMIN_ENABLE', '').lower() not in ('1', 'true', 'yes'):
        return

    username = (os.getenv('BOOTSTRAP_ADMIN_USERNAME') or '').strip()
    email = (os.getenv('BOOTSTRAP_ADMIN_EMAIL') or '').strip().lower()
    full_name = (os.getenv('BOOTSTRAP_ADMIN_FULL_NAME') or '').strip()
    password = os.getenv('BOOTSTRAP_ADMIN_PASSWORD') or ''

    role = (os.getenv('BOOTSTRAP_ADMIN_ROLE') or 'super_admin').strip()
    status = (os.getenv('BOOTSTRAP_ADMIN_STATUS') or 'active').strip()
    must_change = os.getenv('BOOTSTRAP_ADMIN_FORCE_PASSWORD_CHANGE', 'true').lower() in (
        '1', 'true', 'yes'
    )
    reset_existing = os.getenv('BOOTSTRAP_ADMIN_RESET_EXISTING', '').lower() in ('1', 'true', 'yes')

    if not all([username, email, full_name, password]):
        app.logger.error(
            'BOOTSTRAP_ADMIN_ENABLE set but required BOOTSTRAP_ADMIN_* values are missing; skipping bootstrap.'
        )
        return

    with app.app_context():
        from database import Admin

        try:
            db.create_all()
        except Exception as e:
            app.logger.error(f'Bootstrap admin failed during db.create_all(): {e}')
            return

        existing_user = Admin.query.filter_by(username=username).first()
        if existing_user:
            if not reset_existing:
                app.logger.warning(
                    'Bootstrap admin skipped: username already exists. '
                    'Set BOOTSTRAP_ADMIN_RESET_EXISTING=true to reset it.'
                )
                return

            existing_user.email = email
            existing_user.full_name = full_name
            existing_user.role = role
            existing_user.status = status
            existing_user.must_change_password = must_change
            existing_user.set_password(password)
            db.session.commit()
            app.logger.warning(
                f'Bootstrap admin reset: username={username} role={role} status={status}. '
                'Unset BOOTSTRAP_ADMIN_ENABLE now.'
            )
            return

        existing_email = Admin.query.filter_by(email=email).first()
        if existing_email:
            app.logger.error(
                'Bootstrap admin failed: email already exists for another account. '
                'Use a unique BOOTSTRAP_ADMIN_EMAIL.'
            )
            return

        admin = Admin(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            status=status,
            must_change_password=must_change,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        app.logger.warning(
            f'Bootstrap admin created: username={username} role={role} status={status}. '
            'Unset BOOTSTRAP_ADMIN_ENABLE now.'
        )

# Optional one-time-ish DB initialization for production deployments.
# Enable explicitly via env var so local imports don't unexpectedly mutate DB.
if os.getenv('AUTO_INIT_DB', '').lower() in ('1', 'true', 'yes'):
    with app.app_context():
        init_db()

# Hosted recovery: create/reset a super-admin on startup when explicitly enabled.
_bootstrap_admin_if_configured()

# Initialize Mail
from flask_mail import Mail
mail = Mail(app)

# Import routes
from routes.auth import auth_bp
from routes.users import users_bp
from routes.approvals import approvals_bp
from routes.assessments import assessments_bp
from routes.ml_routes import ml_bp
from routes.healthtips import healthtips_bp
from routes.admin_routes import admin_bp
from routes.logs import logs_bp
from routes.notifications import notifications_bp
from routes.reports import reports_bp
from api_docs import docs_bp
from flask_wtf.csrf import generate_csrf

# Exempt lightweight endpoints from rate limits
limiter.exempt(notifications_bp)

# Exempt auth and ML blueprints from CSRF (ML endpoints are
# called via JSON/file uploads from the SPA-style dashboard)
csrf.exempt(auth_bp)
csrf.exempt(ml_bp)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(approvals_bp, url_prefix='/api/approvals')
app.register_blueprint(assessments_bp, url_prefix='/api/assessments')
app.register_blueprint(ml_bp, url_prefix='/api/ml')
app.register_blueprint(healthtips_bp, url_prefix='/api/healthtips')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(logs_bp, url_prefix='/api/logs')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(docs_bp)  # API documentation


@app.route('/api/csrf-token', methods=['GET'])
def get_csrf_token():
    """Return a CSRF token for authenticated session-based API calls."""
    if 'admin_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'csrf_token': generate_csrf()}), 200

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def _get_session_role():
    role = session.get('admin_role')
    if role:
        return role
    try:
        from database import Admin
        admin = Admin.query.get(session.get('admin_id'))
        if admin:
            session['admin_role'] = admin.role
            return admin.role
    except Exception:
        pass
    return None


def role_required(allowed_roles):
    """Template-page role guard.

    Uses the role stored in the session (or looks it up).
    Redirects to dashboard if role is not permitted.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'admin_id' not in session:
                return redirect(url_for('login'))

            role = _get_session_role()
            if role and role in allowed_roles:
                return f(*args, **kwargs)

            return redirect(url_for('dashboard'))

        return decorated_function

    return decorator

# Template routes
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/users')
@login_required
@role_required(['admin', 'super_admin'])
def users():
    return render_template('users.html')

@app.route('/assessments')
@login_required
@role_required(['admin', 'super_admin', 'data_analyst', 'analyst'])
def assessments():
    return render_template('assessments.html')

@app.route('/ml-analytics')
@login_required
@role_required(['admin', 'super_admin', 'data_analyst', 'analyst'])
def ml_analytics():
    return render_template('ml_analytics.html')

@app.route('/healthtips')
@login_required
@role_required(['staff', 'admin', 'super_admin'])
def healthtips():
    return render_template('healthtips.html')

@app.route('/admin')
@login_required
@role_required(['admin', 'super_admin'])
def admin():
    return render_template('admin.html')

@app.route('/approvals')
@login_required
@role_required(['admin', 'super_admin'])
def approvals():
    return render_template('approvals.html')

@app.route('/my-requests')
@login_required
def my_requests():
    return render_template('my_requests.html')

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/change-password')
@login_required
def change_password_page():
    """Render the change password page"""
    return render_template('change_password.html')

@app.route('/forgot-password')
def forgot_password_page():
    """Render the forgot password page"""
    return render_template('forgot_password.html')

@app.route('/reset-password')
def reset_password_page():
    """Render the reset password page"""
    return render_template('reset_password.html')

@app.route('/logs')
@login_required
@role_required(['admin', 'super_admin'])
def logs():
    return render_template('logs.html')

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    app.logger.error(f'Bad Request (400): {str(error)} - Path: {request.path} - IP: {request.remote_addr}')
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    return render_template('errors/400.html'), 400

@app.errorhandler(401)
def unauthorized(error):
    app.logger.warning(f'Unauthorized (401): {str(error)} - Path: {request.path} - IP: {request.remote_addr}')
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Unauthorized', 'message': 'Please login'}), 401
    return redirect(url_for('login'))

@app.errorhandler(403)
def forbidden(error):
    app.logger.warning(f'Forbidden (403): {str(error)} - Path: {request.path} - IP: {request.remote_addr}')
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden', 'message': 'Insufficient permissions'}), 403
    return redirect(url_for('dashboard'))

@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f'Not Found (404): {request.path} - IP: {request.remote_addr}')
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(429)
def ratelimit_handler(error):
    app.logger.warning(f'Rate Limit (429): Path: {request.path} - IP: {request.remote_addr}')
    return jsonify({'error': 'Rate limit exceeded', 'message': 'Too many requests. Please try again later.'}), 429

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Internal Server Error (500): {str(error)} - Path: {request.path} - IP: {request.remote_addr}', exc_info=True)
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(Exception)
def unhandled_exception(error):
    app.logger.error(f'Unhandled Exception: {str(error)} - Path: {request.path} - IP: {request.remote_addr}', exc_info=True)
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'error': 'An unexpected error occurred'}), 500
    return render_template('errors/500.html'), 500

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        app.logger.error(f'Database health check failed: {e}')
        db_status = 'unhealthy'
        return jsonify({
            'status': 'unhealthy',
            'database': db_status
        }), 503
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.now().isoformat()
    }), 200

# Cache monitoring endpoint (admin only)
@app.route('/api/cache/stats')
@login_required
@role_required(['admin', 'super_admin'])
def cache_stats():
    """Get cache statistics for monitoring"""
    try:
        from utils.cache import get_cache_stats
        stats = get_cache_stats()
        return jsonify(stats), 200
    except Exception as e:
        app.logger.error(f'Cache stats error: {e}')
        return jsonify({'error': str(e)}), 500

# Cache clear endpoint (admin only)
@app.route('/api/cache/clear', methods=['POST'])
@login_required
@role_required(['admin', 'super_admin'])
def clear_cache():
    """Clear cache (all or by prefix)"""
    try:
        from utils.cache import invalidate_cache
        prefix = request.json.get('prefix') if request.json else None
        count = invalidate_cache(prefix)
        return jsonify({
            'message': f'Cache cleared successfully',
            'entries_removed': count if prefix else 'all'
        }), 200
    except Exception as e:
        app.logger.error(f'Cache clear error: {e}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5001)
