import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database Configuration
# UNIFIED DATABASE: All tables (mobile app + admin dashboard) in eyecare_db

# Render/12-factor style DB URL (preferred for production)
DATABASE_URL = os.getenv('DATABASE_URL')

# Unified Database Config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'eyecare_db'),
    'charset': os.getenv('DB_CHARSET', 'utf8mb4')
}

# Legacy variable names for backward compatibility
ADMIN_DB_CONFIG = DB_CONFIG  # Points to same unified DB
APP_DB_CONFIG = DB_CONFIG    # Points to same unified DB
MYSQL_CONFIG = DB_CONFIG

# SQLAlchemy Database URI
if DATABASE_URL:
    # SQLAlchemy expects 'postgresql://' (Render may provide 'postgres://')
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
else:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    )

# Legacy URI for backward compatibility
APP_DATABASE_URI = SQLALCHEMY_DATABASE_URI

# Connection Pool Settings
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': int(os.getenv('SQLALCHEMY_POOL_RECYCLE', 3600)),
    'pool_size': int(os.getenv('SQLALCHEMY_POOL_SIZE', 10)),
    'max_overflow': int(os.getenv('SQLALCHEMY_MAX_OVERFLOW', 20))
}

# Flask Settings
SECRET_KEY = os.getenv('SECRET_KEY', 'eyecare-secret-key-2025')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
SQLALCHEMY_TRACK_MODIFICATIONS = False
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/uploads')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))

# Mail Configuration
MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True') == 'True'
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
