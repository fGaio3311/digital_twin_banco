# PR: Event validation and ingestion hardening

## Summary
- Added Pydantic event schemas for validation and normalization.
- Validated and processed events in log handler and ingestion endpoints.
- Centralized event processing with anomaly publishing via mqtt_service.
- Hardened DigitalTwin event ingestion against malformed input.
- Added a modern Next.js frontend and updated Docker Compose for full stack runs.

## Changes
- New schema module: `app/schemas.py`.
- Updated `app/main.py` to:
  - validate and ingest events in login, balance, deposit, pix, and logs upload.
  - route event ingestion through `process_event`.
  - avoid duplicate ingestion via `skip_twin` on logger.
- Updated `app/domain/twin.py` with safer parsing for `info`, `amount`, `balance`.
- Added `frontend/` Next.js app with modern UI.
- Updated `docker-compose.yml` and `Dockerfile` to use `app.main:app`.

## Testing
- Smoke import: `python3 -c "import os; os.environ['DATABASE_URL']='sqlite:///./test.db'; os.environ['TESTING']='1'; os.environ['SECRET_KEY']='dev'; os.environ['MQTT_BROKER_HOST']='localhost'; os.environ['MQTT_BROKER_PORT']='1883'; import importlib; importlib.reload(importlib.import_module('app.main')); print('import ok')"`
- Frontend build: `cd frontend && npm install && npm run build`

## Notes
- MQTT connection failures are non-fatal; events continue to be ingested locally.
