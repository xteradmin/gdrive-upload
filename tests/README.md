# Tests

## Running Tests

```bash
python3 -m pytest tests/
```

## Manual Testing

```bash
# Login
curl -c cookies.txt -X POST http://localhost:8889/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"gdrive2026"}'

# Download file
curl -b cookies.txt -X POST http://localhost:8889/api/download \
  -H "Content-Type: application/json" \
  -d '{"url":"https://proof.ovh.net/files/1Mb.dat","filename":"test.dat"}'

# Check status (replace JOB_ID)
curl -b cookies.txt -X POST http://localhost:8889/api/status \
  -H "Content-Type: application/json" \
  -d '{"id":"JOB_ID"}'
```
