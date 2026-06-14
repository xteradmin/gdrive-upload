# Architecture

## System Overview

GDrive Upload is a Python web service that downloads files from URLs to Google Drive via a local sync directory.

```
Browser/API Client
       │
       ▼
┌─────────────┐
│  WebHandler │  ← HTTP requests
│  (web/)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  APIRouter  │  ← Routes requests
│  (api/)     │
└──────┬──────┘
       │
  ┌────┴────┐
  ▼         ▼
┌──────┐ ┌──────────┐
│ Auth │ │ Download │
│      │ │ Manager  │
└──────┘ └─────┬────┘
               │
               ▼
        ┌──────────────┐
        │  /mnt/gdrive │  ← Local filesystem
        │  -sync/      │
        └──────┬───────┘
               │
               ▼ (rclone sync every 30s)
        ┌──────────────┐
        │ Google Drive │
        └──────────────┘
```

## Module Structure

```
src/
├── main.py              # Entry point, wires everything together
├── config.py            # Environment-based configuration
├── auth/
│   └── handler.py       # Login, sessions, cookie management
├── download/
│   └── manager.py       # Background download jobs with threads
├── api/
│   └── routes.py        # REST API endpoint handlers
├── storage/
│   └── files.py         # File listing and deletion
└── web/
    ├── handler.py       # HTTP request handling
    └── templates/       # HTML pages
```

## Data Flow

### Download Flow
1. Client POSTs URL to `/api/download`
2. APIRouter creates job via DownloadManager
3. DownloadManager spawns background thread
4. Thread downloads file in 1MB chunks
5. Thread updates job status every 0.5s
6. Client polls `/api/status` for progress
7. File saved to `/mnt/gdrive-sync/`
8. rclone syncs to Google Drive within 30s

### Auth Flow
1. Client POSTs credentials to `/api/login`
2. AuthHandler validates credentials
3. Creates session token, stores in memory
4. Returns token via Set-Cookie header
5. Client includes cookie in all requests
6. get_session() extracts token from cookie

## Key Design Decisions

- **No external dependencies** - Python stdlib only (http.server, urllib, json, threading)
- **In-memory sessions** - Simple, fast, lost on restart (acceptable for single-user)
- **Background threads** - Downloads don't block HTTP responses
- **rclone for sync** - Reliable, handles Google Drive API complexities
- **Module structure** - Each feature isolated, easy to understand/modify

## Configuration

All config via environment variables with defaults:
- `GDRIVE_HOST` - Server bind address (default: 0.0.0.0)
- `GDRIVE_PORT` - Server port (default: 8889)
- `GDRIVE_USER` - Login username (default: admin)
- `GDRIVE_PASS` - Login password (default: gdrive2026)
- `GDRIVE_UPLOAD_DIR` - Sync directory (default: /mnt/gdrive-sync)
