import sqlite3
from pathlib import Path
from typing import Any


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                photo_file_id TEXT NOT NULL,
                sphere TEXT NOT NULL,
                activity TEXT NOT NULL,
                instagram TEXT,
                hobby TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        connection.commit()


def save_profile(
    db_path: Path,
    *,
    telegram_id: int,
    full_name: str,
    photo_file_id: str,
    sphere: str,
    activity: str,
    instagram: str | None,
    hobby: str | None,
) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO profiles (
                telegram_id,
                full_name,
                photo_file_id,
                sphere,
                activity,
                instagram,
                hobby
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                full_name = excluded.full_name,
                photo_file_id = excluded.photo_file_id,
                sphere = excluded.sphere,
                activity = excluded.activity,
                instagram = excluded.instagram,
                hobby = excluded.hobby,
                created_at = datetime('now')
            """,
            (
                telegram_id,
                full_name,
                photo_file_id,
                sphere,
                activity,
                instagram,
                hobby,
            ),
        )
        connection.commit()


def get_profile(db_path: Path, telegram_id: int) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM profiles WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        return dict(row) if row else None
