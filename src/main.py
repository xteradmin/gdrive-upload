"""GDrive Upload - Entry point."""

import os
import sys
from http.server import HTTPServer

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import HOST, PORT, AUTH_USER, AUTH_PASS, UPLOAD_DIR, CHUNK_SIZE, TIMEOUT
from auth import AuthHandler
from download import DownloadManager
from api import APIRouter
from web import WebHandler


def main():
    """Start the GDrive Upload server."""
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Initialize components
    auth = AuthHandler(AUTH_USER, AUTH_PASS)
    dm = DownloadManager(UPLOAD_DIR, CHUNK_SIZE, TIMEOUT)
    router = APIRouter(auth, dm, UPLOAD_DIR)

    # Wire up handler
    WebHandler.api_router = router

    # Start server
    server = HTTPServer((HOST, PORT), WebHandler)
    print(f"GDrive Upload running on http://{HOST}:{PORT}")
    print(f"Upload directory: {UPLOAD_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
