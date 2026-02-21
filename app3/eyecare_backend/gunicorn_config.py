# ===========================================
# Gunicorn Production Configuration
# ===========================================
import multiprocessing
import os

# Server Socket
bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker Processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Process naming
proc_name = 'eyecare_backend'

# Logging
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Server Mechanics
daemon = False
pidfile = 'logs/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment and configure for HTTPS)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

def on_starting(server):
    """Called just before the master process is initialized."""
    print("=" * 60)
    print("  EyeCare Backend - Gunicorn Starting")
    print("=" * 60)
    print(f"  Workers: {workers}")
    print(f"  Binding: {bind}")
    print(f"  Environment: {os.getenv('FLASK_ENV', 'production')}")
    print("=" * 60)

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading workers...")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    print(f"Worker {worker.pid} received SIGINT/SIGQUIT")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    print(f"Worker {worker.pid} received SIGABRT")
