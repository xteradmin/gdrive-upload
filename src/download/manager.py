"""Download job management and worker thread."""

import os
import time
import uuid
import threading
import urllib.request
import ssl


class DownloadManager:
    """Manages background download jobs."""

    def __init__(self, upload_dir, chunk_size=1048576, timeout=7200):
        self.upload_dir = upload_dir
        self.chunk_size = chunk_size
        self.timeout = timeout
        self.jobs = {}
        self.lock = threading.Lock()
        self.start_time = time.time()

        # Cleanup thread for old jobs
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        cleanup_thread.start()

    def start(self, url, filename, folder=""):
        """Start a background download. Returns job_id."""
        dest_dir = os.path.join(self.upload_dir, folder) if folder else self.upload_dir
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        with self.lock:
            for j in self.jobs.values():
                if j.get("dest") == dest and j.get("status") in ("queued", "downloading"):
                    return None, "Download already in progress"

            job_id = str(uuid.uuid4())[:8]
            self.jobs[job_id] = {
                "status": "queued",
                "url": url,
                "filename": filename,
                "folder": folder,
                "dest": dest,
                "percent": 0,
                "downloaded": 0,
                "total": 0,
                "speed": 0,
                "elapsed": 0,
                "eta": 0,
                "speed_human": "0 MB/s",
                "downloaded_human": "0 B",
                "total_human": "0 B",
                "eta_human": "-",
                "created": time.time(),
                "error": ""
            }

        t = threading.Thread(target=self._worker, args=(job_id, url, dest, filename), daemon=True)
        t.start()
        return job_id, None

    def get(self, job_id):
        """Get job status."""
        with self.lock:
            return self.jobs.get(job_id)

    def list_jobs(self, status_filter="", limit=50):
        """List jobs with optional filter."""
        with self.lock:
            result = []
            for jid, j in self.jobs.items():
                if status_filter and j.get("status") != status_filter:
                    continue
                result.append({
                    "id": jid,
                    "status": j.get("status"),
                    "filename": j.get("filename", ""),
                    "url": j.get("url", ""),
                    "folder": j.get("folder", ""),
                    "percent": j.get("percent", 0),
                    "speed_human": j.get("speed_human", ""),
                    "downloaded_human": j.get("downloaded_human", ""),
                    "total_human": j.get("total_human", ""),
                    "eta_human": j.get("eta_human", ""),
                    "elapsed": j.get("elapsed", 0),
                    "error": j.get("error", ""),
                    "created": j.get("created", 0)
                })
            result.sort(key=lambda x: x.get("created", 0), reverse=True)
            return result[:limit]

    def cancel(self, job_id):
        """Cancel a download."""
        with self.lock:
            if job_id in self.jobs:
                self.jobs[job_id]["status"] = "cancelled"
                return True
            return False

    def get_stats(self):
        """Get service statistics."""
        with self.lock:
            statuses = {}
            for j in self.jobs.values():
                s = j.get("status", "unknown")
                statuses[s] = statuses.get(s, 0) + 1
            return {
                "total_jobs": len(self.jobs),
                "by_status": statuses,
                "uptime": int(time.time() - self.start_time),
                "memory_mb": round(len(str(self.jobs)) / 1024 / 1024, 2)
            }

    def _cleanup_loop(self):
        """Periodically clean up old completed jobs."""
        while True:
            time.sleep(3600)  # Run every hour
            self._cleanup_old_jobs()

    def _cleanup_old_jobs(self):
        """Remove completed jobs older than 24 hours."""
        cutoff = time.time() - 86400
        with self.lock:
            to_remove = []
            for jid, j in self.jobs.items():
                if j.get("status") in ("done", "error", "cancelled"):
                    if j.get("created", 0) < cutoff:
                        to_remove.append(jid)
            for jid in to_remove:
                del self.jobs[jid]

    def _format_size(self, b):
        if b < 1024: return f"{b} B"
        if b < 1048576: return f"{b/1024:.1f} KB"
        if b < 1073741824: return f"{b/1048576:.1f} MB"
        return f"{b/1073741824:.2f} GB"

    def _format_eta(self, seconds):
        if seconds < 60: return f"{seconds}s"
        if seconds < 3600: return f"{seconds//60}m {seconds%60}s"
        return f"{seconds//3600}h {(seconds%3600)//60}m"

    def _worker(self, job_id, url, dest, filename):
        """Background download worker."""
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            start = time.time()
            with urllib.request.urlopen(req, timeout=self.timeout, context=ctx) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                last_update = 0

                with open(dest, "wb") as f:
                    while True:
                        chunk = resp.read(self.chunk_size)
                        if not chunk:
                            break
                        if self.jobs[job_id].get("status") == "cancelled":
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_update >= 0.5 or downloaded == total:
                            elapsed = now - start
                            speed = downloaded / elapsed / 1048576 if elapsed > 0 else 0
                            pct = (downloaded / total * 100) if total > 0 else 0
                            eta = int((total - downloaded) / (speed * 1048576)) if speed > 0 else 0

                            with self.lock:
                                self.jobs[job_id].update({
                                    "status": "downloading",
                                    "downloaded": downloaded,
                                    "total": total,
                                    "percent": round(pct, 1),
                                    "speed": round(speed, 1),
                                    "elapsed": round(elapsed),
                                    "eta": eta,
                                    "speed_human": f"{speed:.1f} MB/s",
                                    "downloaded_human": self._format_size(downloaded),
                                    "total_human": self._format_size(total),
                                    "eta_human": self._format_eta(eta)
                                })
                            last_update = now

            if self.jobs[job_id].get("status") == "cancelled":
                if os.path.exists(dest):
                    os.remove(dest)
                return

            elapsed = time.time() - start
            size = os.path.getsize(dest)
            speed = size / elapsed / 1048576 if elapsed > 0 else 0

            with self.lock:
                self.jobs[job_id].update({
                    "status": "done",
                    "downloaded": size,
                    "total": size,
                    "percent": 100,
                    "speed": round(speed, 1),
                    "elapsed": round(elapsed),
                    "eta": 0,
                    "speed_human": f"{speed:.1f} MB/s",
                    "downloaded_human": self._format_size(size),
                    "total_human": self._format_size(size),
                    "eta_human": "0s",
                    "size_human": self._format_size(size)
                })

            # Fix ownership and trigger Nextcloud file scan
            import subprocess
            try:
                subprocess.run(["chown", "-R", "1000:100", dest], capture_output=True, timeout=10)
                subprocess.run(
                    ["docker", "exec", "-u", "abc", "nextcloud-zvtygue4a9hhxtw13zvw18b7",
                     "php", "/app/www/public/occ", "files:scan", "--all"],
                    capture_output=True, timeout=30
                )
            except Exception:
                pass

        except Exception as e:
            with self.lock:
                self.jobs[job_id].update({
                    "status": "error",
                    "error": str(e),
                    "eta_human": "-"
                })
            if os.path.exists(dest):
                os.remove(dest)
