"""
Gunicorn configuration file for production deployment.

NOTE: We use 1 worker + threads because the app stores background task state
in-memory (task_manager.py). Multiple workers would have separate memory spaces,
causing polling requests to hit workers that don't have the task data (resulting
in "Analysis task expired" errors). On a 1 vCPU server, 1 worker with threads
is also more efficient than multiple processes.
"""
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker configuration: 1 worker + threads for in-memory task state sharing
workers = 1
threads = 4
worker_class = "gthread"
timeout = 300  # 5 min: Stockfish analysis can take ~60s on 1 vCPU
keepalive = 5

# Restart workers after this many requests to prevent memory leaks
max_requests = 5000
max_requests_jitter = 200

# Logging
accesslog = "/var/log/gunicorn/chesstic_access.log"
errorlog = "/var/log/gunicorn/chesstic_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "chesstic"

# Server mechanics
daemon = False
pidfile = "/var/run/chesstic.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (uncomment and configure when you have SSL certificates)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    # Create log directory if it doesn't exist
    os.makedirs("/var/log/gunicorn", exist_ok=True)
    print("Starting Gunicorn server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading Gunicorn server...")

def when_ready(server):
    """Called just after the server is started."""
    print("Gunicorn server is ready. Spawning workers...")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} was interrupted")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker {worker.pid} was aborted")
