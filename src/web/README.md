# Web Module

HTTP request handler and HTML templates.

## Files

- `handler.py` - WebHandler (BaseHTTPRequestHandler subclass)
- `templates/` - HTML files

## How It Works

1. `WebHandler` extends Python's `BaseHTTPRequestHandler`
2. Routes GET/POST requests
3. GET → serves HTML pages (login, upload, status, docs, ai, prompt)
4. POST → delegates to `APIRouter` for API endpoints
5. Public pages: login, docs, ai, prompt (no auth)
6. Protected pages: upload, status (requires session)
7. Login page redirects to `/` after success
8. Logout destroys session and redirects to `/login`

## Template Files

- `login.html` - Login form
- `upload.html` - Main upload page with active downloads
- `status.html` - All download history with filters
- `docs.html` - Developer API documentation
- `ai.html` - AI agent integration guide
- `prompt.html` - Copy-paste prompt for AI agents
