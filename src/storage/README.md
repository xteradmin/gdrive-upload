# Storage Module

File system operations on the upload directory.

## Files

- `files.py` - list_files(), delete_file()

## Key Functions

```python
from storage import list_files, delete_file

# List all files
files = list_files("/mnt/gdrive-sync")
files = list_files("/mnt/gdrive-sync", folder="downloads")

# Delete a file
ok, error = delete_file("/mnt/gdrive-sync", "file.zip")
ok, error = delete_file("/mnt/gdrive-sync", "downloads", folder="downloads")
```

## File Dict Fields

- `name` - filename
- `is_dir` - true if directory
- `size` - bytes
- `size_human` - "100.0 MB"
- `modified` - "2026-06-14 22:00:00"

## Notes

- Hidden files (starting with .) are excluded
- Directories shown with size "-"
- Returns empty list if directory doesn't exist
