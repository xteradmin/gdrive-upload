"""Configuration constants for GDrive Upload service."""

import os

# Server
HOST = os.environ.get("GDRIVE_HOST", "0.0.0.0")
PORT = int(os.environ.get("GDRIVE_PORT", "8889"))

# Auth
AUTH_USER = os.environ.get("GDRIVE_USER", "admin")
AUTH_PASS = os.environ.get("GDRIVE_PASS", "gdrive2026")

# Storage
UPLOAD_DIR = os.environ.get("GDRIVE_UPLOAD_DIR", "/mnt/gdrive-sync")
LOG_FILE = os.environ.get("GDRIVE_LOG_FILE", "/var/log/gdrive-upload.log")

# Download
CHUNK_SIZE = 1048576  # 1MB read chunks
TIMEOUT = 7200       # 2 hours max download
POLL_INTERVAL = 2    # seconds between status checks

# Session
SESSION_MAX_AGE = 86400  # 24 hours
