<?php
session_start();

$USER = 'admin';
$PASS = 'gdrive2026';

if (!isset($_SERVER['PHP_AUTH_USER']) || $_SERVER['PHP_AUTH_USER'] !== $USER || $_SERVER['PHP_AUTH_PW'] !== $PASS) {
    header('WWW-Authenticate: Basic realm="Google Drive Upload"');
    header('HTTP/1.0 401 Unauthorized');
    echo 'Access denied';
    exit;
}

$UPLOAD_DIR = '/mnt/gdrive-sync';
$log_file = '/var/log/gdrive-upload.log';

function log_msg($msg) {
    global $log_file;
    file_put_contents($log_file, date('Y-m-d H:i:s') . " - $msg\n", FILE_APPEND);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['url'])) {
    $url = trim($_POST['url']);
    $filename = isset($_POST['filename']) && !empty($_POST['filename']) 
        ? trim($_POST['filename']) 
        : basename(parse_url($url, PHP_URL_PATH));
    
    if (empty($filename) || $filename === '/' || $filename === '.') {
        $filename = 'download_' . date('Ymd_His');
    }

    $dest = $UPLOAD_DIR . '/' . $filename;
    $folder = isset($_POST['folder']) && !empty($_POST['folder']) ? trim($_POST['folder']) : '';
    if (!empty($folder)) {
        $dest_folder = $UPLOAD_DIR . '/' . $folder;
        if (!is_dir($dest_folder)) {
            mkdir($dest_folder, 0777, true);
        }
        $dest = $dest_folder . '/' . $filename;
    }

    log_msg("Downloading: $url -> $dest");

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_FILE, fopen($dest, 'w'));
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
    curl_setopt($ch, CURLOPT_MAXREDIRS, 10);
    curl_setopt($ch, CURLOPT_TIMEOUT, 3600);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0');
    
    $fp = fopen($dest, 'w');
    curl_setopt($ch, CURLOPT_FILE, $fp);
    
    $start = time();
    curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $total_size = filesize($dest);
    $elapsed = time() - $start;
    $speed = $elapsed > 0 ? round($total_size / $elapsed / 1024 / 1024, 2) : 0;
    
    fclose($fp);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        log_msg("ERROR: $error");
        unlink($dest);
        $result = ['success' => false, 'error' => $error];
    } elseif ($http_code >= 200 && $http_code < 400) {
        log_msg("OK: $filename ($total_size bytes, {$speed} MB/s, {$elapsed}s)");
        $result = [
            'success' => true,
            'filename' => $filename,
            'size' => $total_size,
            'speed' => $speed,
            'time' => $elapsed
        ];
    } else {
        log_msg("HTTP ERROR: $http_code");
        unlink($dest);
        $result = ['success' => false, 'error' => "HTTP $http_code"];
    }

    header('Content-Type: application/json');
    echo json_encode($result);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'list') {
    $folder = isset($_POST['folder']) ? trim($_POST['folder']) : '';
    $path = $UPLOAD_DIR . '/' . $folder;
    $items = [];
    if (is_dir($path)) {
        foreach (new DirectoryIterator($path) as $item) {
            if ($item->isDot()) continue;
            $items[] = [
                'name' => $item->getFilename(),
                'is_dir' => $item->isDir(),
                'size' => $item->isFile() ? $item->getSize() : 0,
                'modified' => date('Y-m-d H:i:s', $item->getMTime())
            ];
        }
    }
    header('Content-Type: application/json');
    echo json_encode($items);
    exit;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Google Drive - Upload from URL</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; display: flex; justify-content: center; align-items: flex-start; padding: 40px 20px; }
.container { max-width: 700px; width: 100%; }
h1 { font-size: 24px; margin-bottom: 8px; color: #58a6ff; }
.subtitle { color: #8b949e; margin-bottom: 24px; font-size: 14px; }
.form-group { margin-bottom: 16px; }
label { display: block; font-size: 13px; color: #8b949e; margin-bottom: 6px; }
input[type="text"], input[type="url"] { width: 100%; padding: 10px 14px; background: #161b22; border: 1px solid #30363d; border-radius: 6px; color: #c9d1d9; font-size: 14px; outline: none; }
input:focus { border-color: #58a6ff; }
.btn { padding: 10px 24px; background: #238636; border: none; border-radius: 6px; color: #fff; font-size: 14px; cursor: pointer; font-weight: 600; }
.btn:hover { background: #2ea043; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.progress { margin-top: 20px; display: none; }
.progress-bar { height: 6px; background: #21262d; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #58a6ff; width: 0%; transition: width 0.3s; border-radius: 3px; }
.progress-text { font-size: 13px; color: #8b949e; margin-top: 8px; }
.result { margin-top: 16px; padding: 12px 16px; border-radius: 6px; font-size: 14px; display: none; }
.result.success { background: #0d2818; border: 1px solid #238636; color: #3fb950; }
.result.error { background: #2d1013; border: 1px solid #da3633; color: #f85149; }
.history { margin-top: 32px; }
.history h2 { font-size: 16px; margin-bottom: 12px; color: #8b949e; }
.history-item { padding: 8px 12px; background: #161b22; border: 1px solid #21262d; border-radius: 6px; margin-bottom: 6px; font-size: 13px; display: flex; justify-content: space-between; align-items: center; }
.history-item .name { color: #c9d1d9; }
.history-item .meta { color: #8b949e; font-size: 12px; }
</style>
</head>
<body>
<div class="container">
    <h1>Google Drive Upload</h1>
    <p class="subtitle">Download file from URL to Google Drive</p>
    
    <form id="uploadForm">
        <div class="form-group">
            <label>File URL *</label>
            <input type="url" id="url" name="url" placeholder="https://example.com/file.zip" required>
        </div>
        <div class="form-group">
            <label>Filename (optional, auto-detect if empty)</label>
            <input type="text" id="filename" name="filename" placeholder="file.zip">
        </div>
        <div class="form-group">
            <label>Folder (optional)</label>
            <input type="text" id="folder" name="folder" placeholder="subfolder name">
        </div>
        <button type="submit" class="btn" id="submitBtn">Download to Google Drive</button>
    </form>

    <div class="progress" id="progress">
        <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
        <div class="progress-text" id="progressText">Downloading...</div>
    </div>

    <div class="result" id="result"></div>

    <div class="history" id="historySection">
        <h2>Recent Downloads</h2>
        <div id="history"></div>
    </div>
</div>

<script>
const history = [];

document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const btn = document.getElementById('submitBtn');
    const progress = document.getElementById('progress');
    const result = document.getElementById('result');
    
    btn.disabled = true;
    btn.textContent = 'Downloading...';
    progress.style.display = 'block';
    result.style.display = 'none';
    
    const fill = document.getElementById('progressFill');
    const text = document.getElementById('progressText');
    
    let pct = 0;
    const timer = setInterval(() => {
        pct = Math.min(pct + Math.random() * 3, 90);
        fill.style.width = pct + '%';
    }, 500);
    
    text.textContent = 'Downloading file...';
    
    const formData = new FormData();
    formData.append('url', document.getElementById('url').value);
    formData.append('filename', document.getElementById('filename').value);
    formData.append('folder', document.getElementById('folder').value);
    
    try {
        const resp = await fetch('', { method: 'POST', body: formData });
        const data = await resp.json();
        
        clearInterval(timer);
        fill.style.width = '100%';
        
        if (data.success) {
            const sizeMB = (data.size / 1024 / 1024).toFixed(2);
            text.textContent = 'Done! Syncing to Google Drive...';
            result.className = 'result success';
            result.innerHTML = `<strong>${data.filename}</strong><br>${sizeMB} MB | ${data.speed} MB/s | ${data.time}s`;
            history.unshift({ name: data.filename, size: sizeMB, speed: data.speed });
        } else {
            text.textContent = 'Failed';
            result.className = 'result error';
            result.textContent = 'Error: ' + data.error;
        }
        result.style.display = 'block';
    } catch(err) {
        clearInterval(timer);
        text.textContent = 'Failed';
        result.className = 'result error';
        result.textContent = 'Error: ' + err.message;
        result.style.display = 'block';
    }
    
    btn.disabled = false;
    btn.textContent = 'Download to Google Drive';
    setTimeout(() => { progress.style.display = 'none'; }, 3000);
    renderHistory();
});

function renderHistory() {
    const el = document.getElementById('history');
    el.innerHTML = history.map(h => 
        `<div class="history-item"><span class="name">${h.name}</span><span class="meta">${h.size} MB | ${h.speed} MB/s</span></div>`
    ).join('');
}
</script>
</body>
</html>
