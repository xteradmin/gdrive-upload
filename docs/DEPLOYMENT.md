# Deployment

## Docker

```bash
# Build
docker build -t gdrive-upload .

# Run
docker run -d \
  -p 8889:8889 \
  -v /mnt/gdrive-sync:/mnt/gdrive-sync \
  --name gdrive-upload \
  gdrive-upload

# With custom config
docker run -d \
  -p 8889:8889 \
  -v /mnt/gdrive-sync:/mnt/gdrive-sync \
  -e GDRIVE_USER=myuser \
  -e GDRIVE_PASS=mypassword \
  gdrive-upload
```

## Docker Compose

```yaml
version: '3'
services:
  gdrive-upload:
    build: .
    ports:
      - "8889:8889"
    volumes:
      - /mnt/gdrive-sync:/mnt/gdrive-sync
    environment:
      - GDRIVE_USER=admin
      - GDRIVE_PASS=gdrive2026
    restart: unless-stopped
```

## Systemd Service

```ini
[Unit]
Description=GDrive Upload
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/gdrive-upload
ExecStart=/usr/bin/python3 src/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| GDRIVE_HOST | 0.0.0.0 | Bind address |
| GDRIVE_PORT | 8889 | Server port |
| GDRIVE_USER | admin | Login username |
| GDRIVE_PASS | gdrive2026 | Login password |
| GDRIVE_UPLOAD_DIR | /mnt/gdrive-sync | Upload directory |
| GDRIVE_LOG_FILE | /var/log/gdrive-upload.log | Log file path |

## Prerequisites

- Python 3.10+
- rclone configured with Google Drive
- /mnt/gdrive-sync directory exists
- rclone sync service running (syncs local → Google Drive)
