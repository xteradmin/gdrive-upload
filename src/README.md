# Source Code

## Module Structure

```
src/
├── main.py          # Entry point
├── config.py        # Configuration
├── auth/            # Authentication
├── download/        # Download jobs
├── api/             # REST API
├── storage/         # File operations
└── web/             # HTTP handler
```

## Quick Start

```bash
python3 src/main.py
```

## Module Summary

| Module | Purpose | Key File |
|--------|---------|----------|
| auth | Login, sessions | handler.py |
| download | Background jobs | manager.py |
| api | REST endpoints | routes.py |
| storage | File ops | files.py |
| web | HTTP handling | handler.py |

## Adding a New Endpoint

1. Add handler method in `api/routes.py`
2. Add route in `APIRouter._handle_post()`
3. Update `docs/API.md`

## Adding a New Page

1. Create HTML in `web/templates/`
2. Add route in `web/handler.py` `do_GET()`
3. Update navigation in all templates
