import sqlite3
from contextlib import contextmanager
import threading
from datetime import datetime

FIELDS = ("name", "phone", "email", "service", "preferred_date", "preferred_time",
          "reason", "conditions", "medications", "consent")

_db_path = None
_lock = threading.Lock()


@contextmanager
def _connect():
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init(db_path):
    global _db_path
    _db_path = db_path
    with _lock, _connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS requests ("
            "id INTEGER PRIMARY KEY, created_at TEXT, name TEXT, phone TEXT, email TEXT, "
            "service TEXT, preferred_date TEXT, preferred_time TEXT, reason TEXT, "
            "conditions TEXT, medications TEXT, consent INTEGER)"
        )


def add_request(data):
    row = {f: data.get(f, "") for f in FIELDS}
    row["consent"] = 1 if data.get("consent") else 0
    created = datetime.now().isoformat(timespec="seconds")
    with _lock, _connect() as conn:
        cur = conn.execute(
            "INSERT INTO requests (created_at, " + ", ".join(FIELDS) + ") VALUES (?" + ", ?" * len(FIELDS) + ")",
            (created, *[row[f] for f in FIELDS]),
        )
        return cur.lastrowid


def list_requests():
    with _lock, _connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM requests ORDER BY id ASC")]


def get_request(request_id):
    with _lock, _connect() as conn:
        r = conn.execute("SELECT * FROM requests WHERE id = ?", (request_id,)).fetchone()
        return dict(r) if r else None
