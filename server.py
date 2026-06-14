#!/usr/bin/env python3
import http.server
import urllib.request
import json
import os
import time
import threading
import ssl
import uuid
import secrets

UPLOAD_DIR = '/mnt/gdrive-sync'
LOG_FILE = '/var/log/gdrive-upload.log'
AUTH_USER = 'admin'
AUTH_PASS = 'gdrive2026'

jobs = {}
jobs_lock = threading.Lock()
sessions = {}

def log_msg(msg):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def format_size(b):
    if b < 1024: return f"{b} B"
    if b < 1048576: return f"{b/1024:.1f} KB"
    if b < 1073741824: return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.2f} GB"

def format_eta(seconds):
    if seconds < 60: return f"{seconds}s"
    if seconds < 3600: return f"{seconds//60}m {seconds%60}s"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"

def get_session(handler):
    cookie = handler.headers.get('Cookie', '')
    for part in cookie.split(';'):
        kv = part.strip().split('=', 1)
        if len(kv) == 2 and kv[0] == 'session':
            token = kv[1]
            if token in sessions:
                return sessions[token]
    return None

def create_session():
    token = secrets.token_hex(32)
    sessions[token] = {'user': AUTH_USER, 'created': time.time()}
    return token

def download_worker(job_id, url, dest, filename, folder):
    job = jobs[job_id]
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        start = time.time()
        with urllib.request.urlopen(req, timeout=7200, context=ctx) as resp:
            total = int(resp.headers.get('Content-Length', 0))
            downloaded = 0
            last_update = 0
            with open(dest, 'wb') as f:
                while True:
                    chunk = resp.read(1048576)
                    if not chunk:
                        break
                    if jobs[job_id].get('status') == 'cancelled':
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    now = time.time()
                    if now - last_update >= 0.5 or downloaded == total:
                        elapsed = now - start
                        speed = downloaded / elapsed / 1048576 if elapsed > 0 else 0
                        pct = (downloaded / total * 100) if total > 0 else 0
                        eta = int((total - downloaded) / (speed * 1048576)) if speed > 0 else 0
                        with jobs_lock:
                            jobs[job_id].update({
                                'status': 'downloading',
                                'downloaded': downloaded,
                                'total': total,
                                'percent': round(pct, 1),
                                'speed': round(speed, 1),
                                'elapsed': round(elapsed),
                                'eta': eta,
                                'speed_human': f"{speed:.1f} MB/s",
                                'downloaded_human': format_size(downloaded),
                                'total_human': format_size(total),
                                'eta_human': format_eta(eta)
                            })
                        last_update = now

        if jobs[job_id].get('status') == 'cancelled':
            if os.path.exists(dest):
                os.remove(dest)
            log_msg(f"CANCELLED: {filename}")
            return

        elapsed = time.time() - start
        size = os.path.getsize(dest)
        speed = size / elapsed / 1048576 if elapsed > 0 else 0
        with jobs_lock:
            jobs[job_id].update({
                'status': 'done',
                'downloaded': size,
                'total': size,
                'percent': 100,
                'speed': round(speed, 1),
                'elapsed': round(elapsed),
                'eta': 0,
                'speed_human': f"{speed:.1f} MB/s",
                'downloaded_human': format_size(size),
                'total_human': format_size(size),
                'eta_human': '0s',
                'size_human': format_size(size)
            })
        log_msg(f"OK: {filename} ({format_size(size)}, {speed:.1f} MB/s, {elapsed:.0f}s)")

    except Exception as e:
        with jobs_lock:
            jobs[job_id].update({'status': 'error', 'error': str(e), 'eta_human': '-'})
        log_msg(f"ERROR: {e}")
        if os.path.exists(dest):
            os.remove(dest)


class UploadHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def get_session(self):
        return get_session(self)

    def set_session(self, token):
        self.send_header('Set-Cookie', f'session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400')

    def redirect(self, url):
        self.send_response(302)
        self.send_header('Location', url)
        self.end_headers()

    def serve_file(self, path, content_type='text/html'):
        with open(path, 'rb') as f:
            data = f.read()
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', len(data))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, data, code=200):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?')[0]

        if path == '/login':
            self.serve_file('/opt/gdrive-upload/login.html')
            return

        if path == '/logout':
            cookie = self.headers.get('Cookie', '')
            for part in cookie.split(';'):
                kv = part.strip().split('=', 1)
                if len(kv) == 2 and kv[0] == 'session':
                    sessions.pop(kv[1], None)
            self.redirect('/login')
            return

        if path == '/api/me':
            sess = self.get_session()
            if sess:
                self.send_json({'user': sess['user']})
            else:
                self.send_json({'user': None}, 401)
            return

        if path == '/docs' or path == '/docs/':
            self.serve_file('/opt/gdrive-upload/docs.html')
            return

        if path == '/api-docs' or path == '/api-docs/':
            self.serve_file('/opt/gdrive-upload/api-docs.html')
            return

        if path == '/ai' or path == '/ai/' or path == '/ai/copy':
            self.serve_file('/opt/gdrive-upload/ai-docs.html')
            return

        if path == '/prompt':
            self.serve_file('/opt/gdrive-upload/prompt.html')
            return

        sess = self.get_session()
        if not sess:
            self.redirect('/login')
            return

        if path == '/' or path == '/index.html':
            self.serve_file('/opt/gdrive-upload/index.html')
        elif path == '/status':
            self.serve_file('/opt/gdrive-upload/status.html')
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path.split('?')[0]
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        if path == '/api/login':
            try:
                data = json.loads(body)
            except:
                self.send_json({'success': False}, 400)
                return
            if data.get('username') == AUTH_USER and data.get('password') == AUTH_PASS:
                token = create_session()
                self.send_response(200)
                self.set_session(token)
                self.send_header('Content-Type', 'application/json')
                body_out = json.dumps({'success': True}).encode()
                self.send_header('Content-Length', len(body_out))
                self.end_headers()
                self.wfile.write(body_out)
                log_msg(f"Login: {AUTH_USER}")
            else:
                self.send_json({'success': False, 'error': 'Invalid credentials'}, 401)
            return

        sess = self.get_session()
        if not sess:
            self.send_json({'error': 'Unauthorized'}, 401)
            return

        if path == '/api/download':
            self.handle_download(body)
        elif path == '/api/status':
            self.handle_status(body)
        elif path == '/api/cancel':
            self.handle_cancel(body)
        elif path == '/api/delete':
            self.handle_delete(body)
        elif path == '/api/list':
            self.handle_list(body)
        elif path == '/api/jobs':
            self.handle_jobs(body)
        else:
            self.send_error(404)

    def handle_delete(self, body):
        try:
            data = json.loads(body)
        except:
            self.send_json({'success': False, 'error': 'Invalid JSON'}, 400)
            return
        name = data.get('name', '')
        folder = data.get('folder', '')
        if not name:
            self.send_json({'success': False, 'error': 'Name required'}, 400)
            return
        path = os.path.join(UPLOAD_DIR, folder, name) if folder else os.path.join(UPLOAD_DIR, name)
        try:
            if os.path.isdir(path):
                import shutil
                shutil.rmtree(path)
            else:
                os.remove(path)
            log_msg(f"DELETE: {path}")
            self.send_json({'success': True})
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)})

    def handle_jobs(self, body):
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        status_filter = data.get('filter', '')
        limit = data.get('limit', 50)
        with jobs_lock:
            result = []
            for jid, j in list(jobs.items()):
                if status_filter and j.get('status') != status_filter:
                    continue
                result.append({
                    'id': jid,
                    'status': j.get('status'),
                    'filename': j.get('filename', ''),
                    'url': j.get('url', ''),
                    'folder': j.get('folder', ''),
                    'percent': j.get('percent', 0),
                    'speed_human': j.get('speed_human', ''),
                    'downloaded_human': j.get('downloaded_human', ''),
                    'total_human': j.get('total_human', ''),
                    'eta_human': j.get('eta_human', ''),
                    'elapsed': j.get('elapsed', 0),
                    'error': j.get('error', ''),
                    'created': j.get('created', 0)
                })
            result.sort(key=lambda x: x.get('created', 0), reverse=True)
            result = result[:limit]
        self.send_json(result)

    def handle_status(self, body):
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        job_id = data.get('id', '')
        with jobs_lock:
            job = jobs.get(job_id)
        if job:
            self.send_json(job)
        else:
            self.send_json({'error': 'Job not found'}, 404)

    def handle_cancel(self, body):
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        job_id = data.get('id', '')
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id]['status'] = 'cancelled'
                self.send_json({'success': True})
            else:
                self.send_json({'error': 'Job not found'}, 404)

    def handle_list(self, body):
        try:
            data = json.loads(body) if body else {}
        except:
            data = {}
        folder = data.get('folder', '')
        path = os.path.join(UPLOAD_DIR, folder) if folder else UPLOAD_DIR
        items = []
        if os.path.isdir(path):
            for item in sorted(os.listdir(path)):
                if item.startswith('.'):
                    continue
                full = os.path.join(path, item)
                stat = os.stat(full)
                items.append({
                    'name': item,
                    'is_dir': os.path.isdir(full),
                    'size': stat.st_size if os.path.isfile(full) else 0,
                    'size_human': format_size(stat.st_size) if os.path.isfile(full) else '-',
                    'modified': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                })
        self.send_json(items)

    def handle_download(self, body):
        try:
            data = json.loads(body)
        except:
            self.send_json({'success': False, 'error': 'Invalid JSON'}, 400)
            return

        url = data.get('url', '').strip()
        filename = data.get('filename', '').strip()
        folder = data.get('folder', '').strip()

        if not url:
            self.send_json({'success': False, 'error': 'URL is required'}, 400)
            return

        if not filename:
            from urllib.parse import urlparse, unquote
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            if not filename or filename == '/' or filename == '.':
                filename = f"download_{time.strftime('%Y%m%d_%H%M%S')}"

        dest_dir = os.path.join(UPLOAD_DIR, folder) if folder else UPLOAD_DIR
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, filename)

        with jobs_lock:
            for j in jobs.values():
                if j.get('dest') == dest and j.get('status') in ('queued', 'downloading'):
                    self.send_json({'success': False, 'error': 'Download already in progress'})
                    return

        job_id = str(uuid.uuid4())[:8]
        with jobs_lock:
            jobs[job_id] = {
                'status': 'queued',
                'url': url,
                'filename': filename,
                'folder': folder,
                'dest': dest,
                'percent': 0,
                'downloaded': 0,
                'total': 0,
                'speed': 0,
                'elapsed': 0,
                'eta': 0,
                'speed_human': '0 MB/s',
                'downloaded_human': '0 B',
                'total_human': '0 B',
                'eta_human': '-',
                'created': time.time()
            }

        t = threading.Thread(target=download_worker, args=(job_id, url, dest, filename, folder), daemon=True)
        t.start()

        log_msg(f"Queued: {url} -> {dest} (job: {job_id})")
        self.send_json({
            'success': True,
            'job_id': job_id,
            'filename': filename,
            'message': 'Download started in background'
        })

if __name__ == '__main__':
    log_msg("Server started on port 8889")
    server = http.server.HTTPServer(('0.0.0.0', 8889), UploadHandler)
    server.serve_forever()
