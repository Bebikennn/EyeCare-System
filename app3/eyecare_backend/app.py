from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from routes.user import user_bp
from routes.auth import auth_bp
from routes.predict import predict_bp
from routes.health_tips import health_tips_bp
from routes.assessment import assessment_bp
from routes.feedback import feedback_bp
from routes.notifications import notifications_bp
from services.email_service import mail
import config
import socket
import logging
import os
from logging.handlers import RotatingFileHandler

# Initialize Sentry for error tracking and performance monitoring
if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        integrations=[FlaskIntegration()],
        traces_sample_rate=config.SENTRY_TRACES_SAMPLE_RATE,
        environment=config.SENTRY_ENVIRONMENT,
        # Set release version (can be from git commit or environment variable)
        release=os.getenv('APP_VERSION', '1.0.0'),
        # Send error reports to Sentry
        before_send=lambda event, hint: event if not config.DEBUG else None  # Don't send in debug mode
    )
    print(f"✅ Sentry monitoring initialized (Environment: {config.SENTRY_ENVIRONMENT})")
else:
    print("⚠️  Sentry DSN not configured. Error tracking disabled.")

app = Flask(__name__)

# CORS
# - In production, prefer explicit allowlist via CORS_ORIGINS
# - In debug/dev, allow all for convenience
cors_origins_raw = (os.getenv('CORS_ORIGINS') or '').strip()
if config.DEBUG:
    CORS(app)
elif cors_origins_raw:
    allowed_origins = [o.strip() for o in cors_origins_raw.split(',') if o.strip()]
    CORS(app, origins=allowed_origins)

# Configure Swagger API Documentation
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec',
            "route": '/apispec.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "EyeCare Backend API",
        "description": "Comprehensive API documentation for EyeCare mobile application backend",
        "version": "1.0.0",
        "contact": {
            "name": "EyeCare Team",
            "email": "support@eyecare.com"
        }
    },
    "host": f"{config.HOST}:{config.PORT}",
    "basePath": "/",
    "schemes": ["http", "https"],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Example: 'Bearer {token}'"
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Configure secret key for sessions
app.config['SECRET_KEY'] = config.SECRET_KEY

# Configure Flask-Mail
app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_TLS'] = config.MAIL_USE_TLS
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER

# Initialize mail with app
mail.init_app(app)

# Configure rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=config.RATELIMIT_STORAGE_URL,
    enabled=config.RATELIMIT_ENABLED
)

# Apply specific rate limits to auth endpoints
@limiter.limit("5 per minute")
def apply_login_limit():
    pass

# Store limiter in app extensions for blueprint access
app.extensions['limiter'] = limiter

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler(
    'logs/eyecare.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('EyeCare backend startup')

# register blueprints
app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(predict_bp)
app.register_blueprint(health_tips_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(notifications_bp)

# Preload ML model at startup
print("🚀 Preloading ML model...")
try:
    from services.ml_predict import preload_model
    preload_model()
except Exception as e:
    app.logger.warning(f"Failed to preload ML model: {e}")

# Advertise backend on the LAN via mDNS (Zeroconf) for automatic discovery
print("📡 Advertising backend via mDNS (_eyecare._tcp)...")
try:
    from services.mdns_service import start_mdns

    start_mdns(
        port=config.PORT,
        properties={
            "path": "/test",
            "service": "eyecare_backend",
            "version": os.getenv("APP_VERSION", "1.0.0"),
        },
    )
except Exception as e:
    app.logger.warning(f"Failed to start mDNS advertisement: {e}")

def get_local_ip():
    """Get the local IP address of the machine."""
    try:
        # Create a socket to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

# ===============================================
# Health Check and Monitoring Endpoints
# ===============================================

@app.route("/test", methods=["GET"])
def health_check():
    """Basic health check endpoint"""
    return jsonify({"status": "ok", "message": "EyeCare backend is running"}), 200

@app.route("/api/health", methods=["GET"])
def health_detailed():
    """
    Comprehensive health check endpoint
    Returns system status, database connectivity, cache status, etc.
    ---
    tags:
      - Monitoring
    responses:
      200:
        description: System health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": str(__import__('datetime').datetime.now()),
        "version": os.getenv('APP_VERSION', '1.0.0'),
        "environment": config.FLASK_ENV,
        "services": {}
    }
    
    # Check database connection
    try:
        from services.db import get_connection
        conn = get_connection()
        conn.ping()
        conn.close()
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Redis cache
    try:
        from services.cache_service import get_cache_stats
        cache_stats = get_cache_stats()
        if cache_stats.get("enabled"):
            health_status["services"]["cache"] = "healthy"
            health_status["cache_stats"] = cache_stats
        else:
            health_status["services"]["cache"] = "disabled"
    except Exception as e:
        health_status["services"]["cache"] = f"error: {str(e)}"
    
    # Check ML model
    try:
        from services.ml_predict import load_model
        load_model()
        health_status["services"]["ml_model"] = "loaded"
    except Exception as e:
        health_status["services"]["ml_model"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@app.route("/api/server-info", methods=["GET"])
def server_info():
    """Return server IP and port information for auto-configuration."""
    local_ip = get_local_ip()
    return jsonify({
        "status": "success",
        "ip": local_ip,
        "port": 5000,
        "base_url": f"http://{local_ip}:5000"
    }), 200

# ===========================================
# Error Handlers
# ===========================================
@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning(f"404 error: {request.url}")
    return jsonify({"status": "error", "message": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"500 error: {error}")
    return jsonify({"status": "error", "message": "Internal server error"}), 500

@app.errorhandler(429)
def ratelimit_error(error):
    app.logger.warning(f"Rate limit exceeded: {get_remote_address()}")
    return jsonify({"status": "error", "message": "Too many requests. Please try again later."}), 429

@app.errorhandler(Exception)
def handle_exception(error):
    app.logger.error(f"Unhandled exception: {error}", exc_info=True)
    return jsonify({"status": "error", "message": "An unexpected error occurred"}), 500

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("=" * 60)
    print(f"  EyeCare Backend Server Starting")
    print("=" * 60)
    print(f"  Environment: {config.FLASK_ENV}")
    print(f"  Debug Mode: {config.DEBUG}")
    print(f"  Local IP: {local_ip}")
    print(f"  Port: {config.PORT}")
    print(f"  Backend URL: http://{local_ip}:{config.PORT}")
    print(f"  Update Flutter app with: http://{local_ip}:{config.PORT}")
    print(f"  Rate Limiting: {'Enabled' if config.RATELIMIT_ENABLED else 'Disabled'}")
    print("=" * 60)
    
    if config.DEBUG:
        print("⚠️  WARNING: Debug mode is ON. DO NOT use in production!")
        print("=" * 60)
    
    app.logger.info(f"Server starting on {config.HOST}:{config.PORT} (Debug: {config.DEBUG})")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
