# API Reference

## Base URL

```
https://upload.cobaweb.com
```

## Authentication

### Login
```
POST /api/login
Content-Type: application/json

{"username": "admin", "password": "gdrive2026"}

Response: {"success": true}
Set-Cookie: session=<token>
```

All other endpoints require session cookie.

## Endpoints

### Start Download
```
POST /api/download
Cookie: session=<token>
Content-Type: application/json

{
  "url": "https://example.com/file.zip",
  "filename": "file.zip",
  "folder": "downloads"
}

Response: {
  "success": true,
  "job_id": "a1b2c3d4",
  "filename": "file.zip",
  "message": "Download started in background"
}
```

### Check Status
```
POST /api/status
Cookie: session=<token>
Content-Type: application/json

{"id": "a1b2c3d4"}

Response: {
  "status": "downloading",
  "filename": "file.zip",
  "percent": 45.2,
  "speed_human": "12.5 MB/s",
  "downloaded_human": "45.2 MB",
  "total_human": "100.0 MB",
  "eta_human": "4m 23s",
  "elapsed": 3,
  "error": ""
}
```

### List Jobs
```
POST /api/jobs
Cookie: session=<token>
Content-Type: application/json

{"filter": "downloading", "limit": 50}

Response: [{job}, ...]
```

### Health Check
```
POST /api/health

Response: {
  "status": "ok",
  "uptime": 3600,
  "jobs": 5,
  "active_downloads": 2,
  "version": "1.0.0"
}
```

No authentication required.

### Cancel Download
```
POST /api/cancel
Cookie: session=<token>
Content-Type: application/json

{"id": "a1b2c3d4"}

Response: {"success": true}
```

### List Files
```
POST /api/list
Cookie: session=<token>
Content-Type: application/json

{"folder": ""}

Response: [{name, is_dir, size, size_human, modified}, ...]
```

### Delete File
```
POST /api/delete
Cookie: session=<token>
Content-Type: application/json

{"name": "file.zip", "folder": "downloads"}

Response: {"success": true}
```
