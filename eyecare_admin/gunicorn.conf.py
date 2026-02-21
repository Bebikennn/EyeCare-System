import os

# Bind address
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:5001")

# Worker setup
workers = int(os.getenv("GUNICORN_WORKERS", "2"))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gevent")
threads = int(os.getenv("GUNICORN_THREADS", "2"))

# Timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", "60"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# Logging
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Preload app for memory savings
preload_app = True
