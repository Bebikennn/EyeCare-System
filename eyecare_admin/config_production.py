"""
Production Configuration
Secure settings for production deployment
"""
import os
from dotenv import load_dotenv

# Load environment variables
env_file = '.env.production' if os.path.exists('.env.production') else '.env'
load_dotenv(env_file)

# Flask Settings
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY or SECRET_KEY == 'e3e0a847e40f0479ef7f6fe921db824d54a20b4c2a659c4d611a2d9c72691278':
    raise ValueError("SECRET_KEY must be set in production environment")

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
FLASK_ENV = os.getenv('FLASK_ENV', 'production')

# Validate production settings
if FLASK_ENV == 'production':
    if DEBUG:
        raise ValueError("DEBUG must be False in production")
    if not os.getenv('SENTRY_DSN'):
        print("Warning: SENTRY_DSN not set. Error tracking disabled.")

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'eyecare_db'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

# Validate database credentials in production
if FLASK_ENV == 'production' and not DATABASE_URL and not DB_CONFIG['password']:
    raise ValueError("Database password (DB_PASSWORD) must be set in production when DATABASE_URL is not provided")

# SQLAlchemy Database URI
if DATABASE_URL:
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    )

# Connection Pool Settings
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600)),
    'pool_size': int(os.getenv('SQLALCHEMY_POOL_SIZE', 20)),
    'max_overflow': int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 40))
}

SQLALCHEMY_TRACK_MODIFICATIONS = False

# Redis Configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'password': os.getenv('REDIS_PASSWORD', None),
    'db': int(os.getenv('REDIS_DB', 0))
}

# Mail Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

# Sentry Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', FLASK_ENV)
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', 0.1))

# Security Settings
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() == 'true'
SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
SESSION_LIFETIME_HOURS = int(os.getenv('SESSION_LIFETIME_HOURS', 2))

# Server Configuration
SERVER_NAME = os.getenv('SERVER_NAME')
PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https')

# Application Settings
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))

# Rate Limiting
RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'redis://localhost:6379/1')
RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '5000 per day;1000 per hour')

# CORS
# Comma-separated list of allowed origins.
# Example: https://admin.example.com,https://www.admin.example.com
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '')
