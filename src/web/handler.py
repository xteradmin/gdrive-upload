"""HTTP request handler."""

import os
import json
from http.server import BaseHTTPRequestHandler

# Import modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth import get_session, create_session, destroy_session
from api import APIRouter


TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


class WebHandler(BaseHTTPRequestHandler):
    """HTTP request handler for GDrive Upload."""

    api_router = None  # Set by main.py

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        path = self.path.split("?")[0]

        # Public pages
        if path == "/login":
            return self._serve("login.html")

        if path == "/logout":
            self._destroy_session()
            return self._redirect("/login")

        if path == "/api/me":
            session = get_session(self)
            if session:
                return self._json({"user": session["user"]})
            return self._json({"user": None}, 401)

        # Public docs
        if path in ("/docs", "/docs/"):
            return self._serve("docs.html")
        if path in ("/ai", "/ai/"):
            return self._serve("ai.html")
        if path == "/prompt":
            return self._serve("prompt.html")

        # Protected pages
        session = get_session(self)
        if not session:
            return self._redirect("/login")

        if path in ("/", "/index.html"):
            return self._serve("upload.html")
        if path == "/status":
            return self._serve("status.html")

        self.send_error(404)

    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length > 0 else {}

        # Login endpoint
        if path == "/api/login":
            success, result = self.api_router.auth.login(None, body)
            if success:
                self.send_response(200)
                self.send_header("Set-Cookie", f"session={result}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400")
                self.send_header("Content-Type", "application/json")
                data = json.dumps({"success": True}).encode()
                self.send_header("Content-Length", len(data))
                self.end_headers()
                self.wfile.write(data)
                return
            return self._json({"success": False, "error": result}, 401)

        # Protected endpoints
        session = get_session(self)
        response, code = self.api_router.handle(path, "POST", body, session)
        if isinstance(response, dict) and "error" in response and code == 401:
            return self._json(response, code)
        return self._json(response, code)

    def _serve(self, filename):
        """Serve an HTML file."""
        filepath = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(filepath):
            self.send_error(404)
            return
        with open(filepath, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def _json(self, data, code=200):
        """Send JSON response."""
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _redirect(self, url):
        """Send redirect response."""
        self.send_response(302)
        self.send_header("Location", url)
        self.end_headers()

    def _destroy_session(self):
        """Destroy session from cookie."""
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            kv = part.strip().split("=", 1)
            if len(kv) == 2 and kv[0] == "session":
                destroy_session(kv[1])
