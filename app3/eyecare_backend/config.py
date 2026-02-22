import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in the same directory as this config
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ===========================================
# Database Configuration
# ===========================================
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'eyecare_db')

# ===========================================
# Email Configuration (SMTP)
#
# Notes:
# - Render often blocks consumer SMTP (e.g. Gmail). Prefer Mailjet/SendGrid.
# - Mailjet SMTP uses host `in-v3.mailjet.com` and credentials = API key/secret.
# ===========================================
_mailjet_smtp_user = (os.getenv('MAILJET_SMTP_USERNAME') or os.getenv('MAILJET_API_KEY') or os.getenv('MAILJET_API') or '').strip()
_mailjet_smtp_pass = (os.getenv('MAILJET_SMTP_PASSWORD') or os.getenv('MAILJET_API_SECRET') or '').strip()

MAIL_USERNAME = (os.getenv('MAIL_USERNAME') or _mailjet_smtp_user).strip()
MAIL_PASSWORD = (os.getenv('MAIL_PASSWORD') or _mailjet_smtp_pass).strip()

_default_smtp_server = 'in-v3.mailjet.com' if (MAIL_USERNAME and MAIL_PASSWORD and _mailjet_smtp_user and _mailjet_smtp_pass) else 'smtp.gmail.com'
MAIL_SERVER = os.getenv('MAIL_SERVER', _default_smtp_server)
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() == 'true'

MAIL_DEFAULT_SENDER = os.getenv(
	'MAIL_DEFAULT_SENDER',
	(os.getenv('MAILJET_FROM_EMAIL') or MAIL_USERNAME or 'noreply@eyecare.com'),
)

# ===========================================
# Security Configuration
# ===========================================
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-change-in-production')

# ===========================================
# Application Configuration
# ===========================================
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', 5000))

# ===========================================
# Rate Limiting Configuration
# ===========================================
RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'

# ===========================================
# Verification Settings
# ===========================================
VERIFICATION_CODE_EXPIRY = 600  # 10 minutes in seconds

# ===========================================
# Redis Cache Configuration
# ===========================================
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# ===========================================
# Database Pool Configuration
# ===========================================
DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))

# ===========================================
# Monitoring Configuration (Sentry)
# ===========================================
SENTRY_DSN = os.getenv('SENTRY_DSN', '')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', FLASK_ENV)
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '0.1'))
