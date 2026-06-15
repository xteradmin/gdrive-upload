# GDrive Upload

Background file download service that saves files from any URL to Google Drive with Nextcloud integration.

## Features

- **Background Downloads** - Download files from any URL, runs in background
- **Google Drive Sync** - Auto-sync to Google Drive via rclone
- **Nextcloud Integration** - Files appear in Nextcloud automatically
- **Web UI** - Upload from URL with progress tracking
- **REST API** - Full API for automation and AI agents
- **Health Check** - Monitor service status

## Quick Start

```bash
# Run directly
python3 src/main.py

# Run with Docker
docker build -t gdrive-upload .
docker run -p 8889:8889 -v /mnt/gdrive-sync:/mnt/gdrive-sync gdrive-upload
```

## Access

- URL: `https://upload.cobaweb.com`
- Username: `admin`
- Password: `gdrive2026`

## Architecture

```
src/
├── main.py          # Entry point, starts server
├── config.py        # Configuration (env vars)
├── auth/            # Login, sessions, cookies
├── download/        # Background download jobs
├── api/             # REST API endpoints
├── storage/         # File operations on disk
└── web/             # HTTP handler, HTML pages
```

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/login` | POST | No | Login, get session |
| `/api/download` | POST | Yes | Start background download |
| `/api/status` | POST | Yes | Check job progress |
| `/api/jobs` | POST | Yes | List all jobs |
| `/api/cancel` | POST | Yes | Cancel a download |
| `/api/list` | POST | Yes | List files |
| `/api/delete` | POST | Yes | Delete a file |
| `/api/health` | POST | No | Health check |

## Configuration

All config via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| GDRIVE_HOST | 0.0.0.0 | Bind address |
| GDRIVE_PORT | 8889 | Server port |
| GDRIVE_USER | admin | Login username |
| GDRIVE_PASS | gdrive2026 | Login password |
| GDRIVE_UPLOAD_DIR | /mnt/gdrive-sync | Upload directory |

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System overview
- [API Reference](docs/API.md) - Endpoint details
- [Deployment](docs/DEPLOYMENT.md) - Deploy guide
- [AI Agent Prompt](docs/PROMPT.md) - Copy-paste prompt for AI

## License

MIT
