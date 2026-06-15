"""API route handling - maps endpoints to actions."""

import os
import time
import json
from urllib.parse import urlparse, unquote


class APIRouter:
    """Routes API requests to appropriate handlers."""

    def __init__(self, auth_handler, download_manager, upload_dir):
        self.auth = auth_handler
        self.dm = download_manager
        self.upload_dir = upload_dir
        self.start_time = time.time()

    def handle(self, path, method, body, session):
        """Route request to handler. Returns (response_data, status_code)."""
        if method == "POST":
            return self._handle_post(path, body, session)
        return {"error": "Not found"}, 404

    def _handle_post(self, path, body, session):
        """Handle POST requests."""
        # Public endpoints
        if path == "/api/login":
            return self._login(body)

        if path == "/api/health":
            return self._health()

        # Protected endpoints
        if not session:
            return {"error": "Unauthorized"}, 401

        handlers = {
            "/api/download": self._download,
            "/api/status": self._status,
            "/api/jobs": self._jobs,
            "/api/cancel": self._cancel,
            "/api/list": self._list,
            "/api/delete": self._delete,
        }

        handler = handlers.get(path)
        if handler:
            return handler(body)

        return {"error": "Not found"}, 404

    def _health(self):
        """Health check endpoint."""
        stats = self.dm.get_stats()
        return {
            "status": "ok",
            "uptime": int(time.time() - self.start_time),
            "jobs": stats["total_jobs"],
            "active_downloads": stats["by_status"].get("downloading", 0),
            "version": "1.0.0"
        }, 200

    def _login(self, body):
        """Handle login."""
        success, result = self.auth.login(None, body)
        if success:
            return {"success": True}, 200, result  # result is token
        return {"success": False, "error": result}, 401

    def _download(self, body):
        """Start a download."""
        url = body.get("url", "").strip()
        filename = body.get("filename", "").strip()
        folder = body.get("folder", "").strip()

        if not url:
            return {"success": False, "error": "URL is required"}, 400

        if not filename:
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            if not filename or filename == "/" or filename == ".":
                filename = f"download_{time.strftime('%Y%m%d_%H%M%S')}"

        job_id, error = self.dm.start(url, filename, folder)
        if error:
            return {"success": False, "error": error}, 409

        return {
            "success": True,
            "job_id": job_id,
            "filename": filename,
            "message": "Download started in background"
        }, 200

    def _status(self, body):
        """Get job status."""
        job_id = body.get("id", "")
        job = self.dm.get(job_id)
        if job:
            return job, 200
        return {"error": "Job not found"}, 404

    def _jobs(self, body):
        """List jobs."""
        status_filter = body.get("filter", "")
        limit = body.get("limit", 50)
        return self.dm.list_jobs(status_filter, limit), 200

    def _cancel(self, body):
        """Cancel a download."""
        job_id = body.get("id", "")
        if self.dm.cancel(job_id):
            return {"success": True}, 200
        return {"error": "Job not found"}, 404

    def _list(self, body):
        """List files."""
        from storage import list_files
        folder = body.get("folder", "")
        return list_files(self.upload_dir, folder), 200

    def _delete(self, body):
        """Delete a file."""
        from storage import delete_file
        name = body.get("name", "")
        folder = body.get("folder", "")
        ok, error = delete_file(self.upload_dir, name, folder)
        if ok:
            return {"success": True}, 200
        return {"success": False, "error": error}, 400
