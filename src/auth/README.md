# Auth Module

Handles user authentication and session management.

## Files

- `handler.py` - Login logic, session create/get/destroy, cookie parsing

## Key Functions

- `create_session()` → token string
- `get_session(handler)` → session dict or None
- `destroy_session(token)` → None
- `AuthHandler.authenticate(user, pass)` → bool
- `AuthHandler.login(handler, data)` → (bool, token|error)
- `AuthHandler.check(handler)` → session or None

## How It Works

1. Client POSTs to `/api/login` with username/password
2. AuthHandler validates credentials
3. If valid, creates session token, stores in `sessions` dict
4. Token returned via `Set-Cookie` header
5. All subsequent requests include cookie
6. `get_session()` extracts token from cookie, looks up session

## Sessions Storage

In-memory dict: `{token: {"user": "admin", "created": timestamp}}`
No database needed. Sessions lost on server restart.
