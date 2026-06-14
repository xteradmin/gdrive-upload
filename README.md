# GDrive Upload

Background file download service that saves files from any URL to Google Drive.

## Quick Start

```bash
# Run directly
python3 src/main.py

# Run with Docker
docker build -t gdrive-upload .
docker run -p 8889:8889 gdrive-upload
```

## Access

- URL: `http://localhost:8889`
- Username: `admin`
- Password: `gdrive2026`

## Architecture

```
src/
├── main.py          # Entry point, starts server
├── config.py        # Configuration constants
├── auth/            # Login, sessions, cookies
├── download/        # Background download jobs
├── api/             # REST API endpoints
├── storage/         # File operations on disk
└── web/             # HTTP handler, HTML pages
```

## For AI Agents

Read `docs/ARCHITECTURE.md` for system overview.
Read `docs/API.md` for endpoint reference.
Read `docs/PROMPT.md` for copy-paste prompt.

## License

MIT
