"""Authentication handler - login, sessions, cookies."""

import time
import secrets
import threading

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
                session = sessions[token]
                # Check if session expired
                if time.time() - session.get("created", 0) > 86400:
                    del sessions[token]
                    return None
                return session
    return None


def destroy_session(token):
    """Remove a session."""
    sessions.pop(token, None)


def cleanup_sessions():
    """Remove expired sessions."""
    cutoff = time.time() - 86400
    expired = [t for t, s in sessions.items() if s.get("created", 0) < cutoff]
    for t in expired:
        del sessions[t]


class SessionCleanup(threading.Thread):
    """Background thread to clean up expired sessions."""

    def __init__(self):
        super().__init__(daemon=True)
        self.start()

    def run(self):
        while True:
            time.sleep(3600)  # Run every hour
            cleanup_sessions()


# Start cleanup thread on import
SessionCleanup()


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
