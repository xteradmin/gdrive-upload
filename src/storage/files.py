"""File system operations for upload directory."""

import os
import time
import shutil


def format_size(b):
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    if b < 1073741824: return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.2f} GB"


def list_files(upload_dir, folder=""):
    """List files in upload directory."""
    path = os.path.join(upload_dir, folder) if folder else upload_dir
    items = []

    if not os.path.isdir(path):
        return items

    for item in sorted(os.listdir(path)):
        if item.startswith("."):
            continue
        full = os.path.join(path, item)
        stat = os.stat(full)
        items.append({
            "name": item,
            "is_dir": os.path.isdir(full),
            "size": stat.st_size if os.path.isfile(full) else 0,
            "size_human": format_size(stat.st_size) if os.path.isfile(full) else "-",
            "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
        })

    return items


def delete_file(upload_dir, name, folder=""):
    """Delete a file or directory."""
    if not name:
        return False, "Name required"

    path = os.path.join(upload_dir, folder, name) if folder else os.path.join(upload_dir, name)

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True, None
    except Exception as e:
        return False, str(e)
