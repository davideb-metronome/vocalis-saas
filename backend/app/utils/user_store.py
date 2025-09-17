import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime, timezone


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DB_PATH = DATA_DIR / "vocalis.sqlite"


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                customer_id TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                first_name TEXT,
                full_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def upsert_user(customer_id: str, email: str, first_name: Optional[str], full_name: Optional[str]):
    conn = _connect()
    try:
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            """
            INSERT INTO users(customer_id, email, first_name, full_name, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                email=excluded.email,
                first_name=excluded.first_name,
                full_name=excluded.full_name
            """,
            (customer_id, email, first_name, full_name, now),
        )
        conn.commit()
    finally:
        conn.close()


def get_user_by_customer_id(customer_id: str) -> Optional[Dict[str, str]]:
    conn = _connect()
    try:
        cur = conn.execute(
            "SELECT customer_id, email, first_name, full_name FROM users WHERE customer_id = ?",
            (customer_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "customer_id": row[0],
            "email": row[1],
            "first_name": row[2] or "",
            "full_name": row[3] or "",
        }
    finally:
        conn.close()

