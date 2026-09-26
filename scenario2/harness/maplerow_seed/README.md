# Maple Row Physiotherapy — appointment requests

Small Python web app: patients fill in an appointment-request and intake form; staff review requests at `/admin`.

## Run

    cp .env.example .env
    python3 server.py

Then open http://127.0.0.1:8000/ (admin: user `admin`, password from `ADMIN_PASSWORD` in `.env`).

## Test

    python3 -m unittest -v

## Layout

- `server.py` — HTTP server and routes
- `store.py` — SQLite storage
- `notify.py` — email helper (`NOTIFY_MODE=file` writes `.eml` files to `OUTBOX_DIR`)
- `templates/`, `static/` — pages, CSS and JS
- `tests/` — unit tests
- `fixtures/sample_requests.json` — sample data
- `tickets/` — client tickets
