"""Plain psycopg2 connection helper for ETL scripts.

Unlike database.py (the Streamlit layer), this module has no streamlit
dependency and reads DATABASE_URL from the environment (or .env next to
this file).
"""
import os
from contextlib import contextmanager

import psycopg2


def _load_dotenv() -> None:
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def get_database_url() -> str:
    _load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set. Copy etl/.env.example to etl/.env "
            "or export it in the environment."
        )
    return url


@contextmanager
def connect():
    conn = psycopg2.connect(get_database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
