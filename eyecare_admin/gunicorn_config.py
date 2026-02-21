# Gunicorn WSGI Server Configuration
# For production deployment

# Server socket
bind = "127.0.0.1:8000"  # Bind to localhost (Nginx will proxy)
backlog = 2048

# Worker processes
workers = 4  # (2 x CPU cores) + 1
worker_class = "gevent"  # Use gevent for better concurrency
worker_connections = 1000
max_requests = 1000  # Restart workers after 1000 requests (prevent memory leaks)
max_requests_jitter = 50
timeout = 120
keepalive = 5

# Process naming
proc_name = "eyecare_admin"

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Server mechanics
daemon = False  # Don't run as daemon (systemd will handle this)
pidfile = "logs/gunicorn.pid"
umask = 0o007
user = None  # Run as current user
group = None  # Run as current group
tmp_upload_dir = None

# SSL (if terminating SSL at Gunicorn instead of Nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Server hooks
def on_starting(server):
    print("Starting Gunicorn server...")

def on_reload(server):
    print("Reloading Gunicorn server...")

def when_ready(server):
    print(f"Gunicorn server is ready. Listening on: {server.cfg.bind}")

def on_exit(server):
    print("Shutting down Gunicorn server...")

# Environment variables
raw_env = [
    'FLASK_ENV=production',
]
