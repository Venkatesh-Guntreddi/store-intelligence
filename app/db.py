import sqlite3
from pathlib import Path

DB_PATH = Path("store_intelligence.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            store_id TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            visitor_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            zone_id TEXT,
            dwell_ms INTEGER NOT NULL,
            is_staff INTEGER NOT NULL,
            confidence REAL NOT NULL,
            metadata TEXT NOT NULL
        )
        """
    )

    conn.commit()
    conn.close()