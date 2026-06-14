# API Module

REST API endpoint routing and handlers.

## Files

- `routes.py` - APIRouter class

## Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/login` | POST | No | Login, get session cookie |
| `/api/download` | POST | Yes | Start background download |
| `/api/status` | POST | Yes | Get job progress |
| `/api/jobs` | POST | Yes | List all jobs |
| `/api/cancel` | POST | Yes | Cancel a download |
| `/api/list` | POST | Yes | List files in Google Drive |
| `/api/delete` | POST | Yes | Delete a file |

## Request/Response Format

All requests: `Content-Type: application/json`
All responses: JSON with status code

## How Routing Works

1. `APIRouter.handle()` receives path, method, body, session
2. For `/api/login` → calls `_login()` (no auth needed)
3. For other endpoints → checks session, returns 401 if invalid
4. Routes to appropriate handler method
5. Returns (response_dict, status_code)
