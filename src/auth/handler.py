"""Authentication handler - login, sessions, cookies."""

import time
import secrets
from http.cookies import SimpleCookie

sessions = {}


def create_session():
    """Create a new session and return the token."""
    token = secrets.token_hex(32)
    sessions[token] = {"user": "admin", "created": time.time()}
    return token


def get_session(handler):
    """Extract session from request cookies."""
    cookie_header = handler.headers.get("Cookie", "")
    for part in cookie_header.split(";"):
        kv = part.strip().split("=", 1)
        if len(kv) == 2 and kv[0] == "session":
            token = kv[1]
            if token in sessions:
                return sessions[token]
    return None


def destroy_session(token):
    """Remove a session."""
    sessions.pop(token, None)


class AuthHandler:
    """Handles authentication logic."""

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def authenticate(self, username, password):
        """Check credentials."""
        return username == self.username and password == self.password

    def login(self, handler, data):
        """Process login request. Returns (success, token_or_error)."""
        if self.authenticate(data.get("username", ""), data.get("password", "")):
            token = create_session()
            return True, token
        return False, "Invalid credentials"

    def check(self, handler):
        """Check if request has valid session. Returns session or None."""
        return get_session(handler)
