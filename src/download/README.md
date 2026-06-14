# Download Module

Manages background file downloads from URLs.

## Files

- `manager.py` - DownloadManager class with job tracking and worker thread

## Key Class: DownloadManager

```python
dm = DownloadManager(upload_dir="/mnt/gdrive-sync")

# Start download
job_id, error = dm.start(url="https://example.com/file.zip", filename="file.zip", folder="downloads")

# Check status
job = dm.get(job_id)  # Returns dict with status, percent, speed, etc.

# List all jobs
jobs = dm.list_jobs(status_filter="downloading", limit=50)

# Cancel
dm.cancel(job_id)
```

## Job Status Flow

```
queued → downloading → done
                  ↘ error
                  ↘ cancelled
```

## Job Dict Fields

- `id` - 8-char UUID
- `status` - queued/downloading/done/error/cancelled
- `url` - source URL
- `filename` - destination filename
- `folder` - subfolder
- `percent` - 0-100
- `speed_human` - "12.5 MB/s"
- `downloaded_human` - "45.2 MB"
- `total_human` - "100.0 MB"
- `eta_human` - "4m 23s"
- `elapsed` - seconds
- `error` - error message if failed
- `created` - timestamp

## How Worker Thread Works

1. Creates HTTP request with SSL context (skip verification)
2. Streams response in 1MB chunks
3. Updates job status every 0.5 seconds
4. Checks for cancellation between chunks
5. On completion, sets status to "done"
6. On error, sets status to "error" and cleans up file
