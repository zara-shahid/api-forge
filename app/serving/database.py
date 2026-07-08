"""SQLite persistence — zero extra dependencies, survives restarts."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "forge.db"


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS apis (
                api_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                prompt TEXT,
                entities_json TEXT NOT NULL,
                routes_json TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS entity_records (
                api_id TEXT NOT NULL,
                entity_name TEXT NOT NULL,
                records_json TEXT NOT NULL,
                PRIMARY KEY (api_id, entity_name),
                FOREIGN KEY (api_id) REFERENCES apis(api_id)
            );
            """
        )
