import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                city TEXT,
                niche TEXT,
                instagram TEXT,
                goal TEXT,
                intro TEXT,
                tariff TEXT NOT NULL DEFAULT 'Business',
                tariff_until TEXT,
                joined_at TEXT,
                referred_by INTEGER,
                referral_code TEXT UNIQUE,
                notifications_enabled INTEGER NOT NULL DEFAULT 1,
                is_member INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                amount TEXT,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
            );
            """
        )
        connection.commit()
        _seed_demo_members(connection)


def _seed_demo_members(connection: sqlite3.Connection) -> None:
    count = connection.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    if count > 0:
        return

    demo = [
        (1001, "maria_cosmo", "Мария", "Белград", "Косметологи", "https://instagram.com/maria_cosmo", "Клиентов"),
        (1002, "mark_ads", "Марк", "Белград", "Маркетологи", "https://instagram.com/mark_ads", "Партнеров"),
        (1003, "elena_realty", "Елена", "Нови-Сад", "Риелторы", "https://instagram.com/elena_realty", "Клиентов"),
        (1004, "ivan_photo", "Иван", "Белград", "Фотографы", "https://instagram.com/ivan_photo", "Новые знакомства"),
        (1005, "sara_law", "Сара", "Ниш", "Юристы", "https://instagram.com/sara_law", "Партнеров"),
        (1006, "daria_beauty", "Дарья", "Белград", "Салоны красоты", "https://instagram.com/daria_beauty", "Клиентов"),
        (1007, "nikita_it", "Никита", "Нови-Сад", "IT", "https://instagram.com/nikita_it", "Партнеров"),
        (1008, "olga_food", "Ольга", "Белград", "Рестораны", "https://instagram.com/olga_food", "Развитие личного бренда"),
    ]
    until = (datetime.utcnow() + timedelta(days=30)).strftime("%d.%m.%Y")
    for telegram_id, username, full_name, city, niche, instagram, goal in demo:
        connection.execute(
            """
            INSERT INTO users (
                telegram_id, username, full_name, city, niche, instagram, goal,
                tariff, tariff_until, joined_at, referral_code, is_member, intro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Business', ?, datetime('now'), ?, 1, ?)
            """,
            (
                telegram_id,
                username,
                full_name,
                city,
                niche,
                instagram,
                goal,
                until,
                f"demo{telegram_id}",
                f"Привет! Я {full_name}, сфера — {niche}. Открыта к коллаборациям.",
            ),
        )
    connection.commit()


def _new_referral_code() -> str:
    return secrets.token_hex(4)


def get_user(db_path: Path, telegram_id: int) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE telegram_id = ?",
            (telegram_id,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_referral_code(db_path: Path, code: str) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE referral_code = ?",
            (code,),
        ).fetchone()
        return dict(row) if row else None


def ensure_user(
    db_path: Path,
    telegram_id: int,
    username: str | None,
    referred_by: int | None = None,
) -> dict[str, Any]:
    existing = get_user(db_path, telegram_id)
    if existing:
        with get_connection(db_path) as connection:
            connection.execute(
                "UPDATE users SET username = ? WHERE telegram_id = ?",
                (username, telegram_id),
            )
            connection.commit()
        return get_user(db_path, telegram_id)  # type: ignore[return-value]

    code = _new_referral_code()
    with get_connection(db_path) as connection:
        while connection.execute(
            "SELECT 1 FROM users WHERE referral_code = ?",
            (code,),
        ).fetchone():
            code = _new_referral_code()

        connection.execute(
            """
            INSERT INTO users (telegram_id, username, referred_by, referral_code)
            VALUES (?, ?, ?, ?)
            """,
            (telegram_id, username, referred_by, code),
        )
        connection.commit()
    return get_user(db_path, telegram_id)  # type: ignore[return-value]


def complete_onboarding(
    db_path: Path,
    *,
    telegram_id: int,
    full_name: str,
    city: str,
    niche: str,
    instagram: str,
    goal: str,
) -> None:
    until = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET full_name = ?,
                city = ?,
                niche = ?,
                instagram = ?,
                goal = ?,
                tariff = 'Business',
                tariff_until = ?,
                joined_at = datetime('now'),
                is_member = 1
            WHERE telegram_id = ?
            """,
            (full_name, city, niche, instagram, goal, until, telegram_id),
        )
        connection.commit()


def update_intro(db_path: Path, telegram_id: int, intro: str) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE users SET intro = ? WHERE telegram_id = ?",
            (intro, telegram_id),
        )
        connection.commit()


def set_notifications(db_path: Path, telegram_id: int, enabled: bool) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE users SET notifications_enabled = ? WHERE telegram_id = ?",
            (1 if enabled else 0, telegram_id),
        )
        connection.commit()


def list_by_niche(db_path: Path, niche: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1 AND niche = ?
            ORDER BY joined_at DESC
            LIMIT ?
            """,
            (niche, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def list_new_members(db_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1
            ORDER BY joined_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def search_members(db_path: Path, query: str, limit: int = 15) -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1 AND (
                full_name LIKE ? OR niche LIKE ? OR city LIKE ? OR goal LIKE ? OR intro LIKE ?
            )
            ORDER BY joined_at DESC
            LIMIT ?
            """,
            (like, like, like, like, like, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def count_referrals(db_path: Path, telegram_id: int) -> int:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS c FROM users WHERE referred_by = ? AND is_member = 1",
            (telegram_id,),
        ).fetchone()
        return int(row["c"])


def list_payments(db_path: Path, telegram_id: int) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM payments
            WHERE telegram_id = ?
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (telegram_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def admin_stats(db_path: Path) -> dict[str, Any]:
    with get_connection(db_path) as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS c FROM users WHERE is_member = 1"
        ).fetchone()["c"]
        by_city = connection.execute(
            """
            SELECT city, COUNT(*) AS c FROM users
            WHERE is_member = 1 AND city IS NOT NULL
            GROUP BY city ORDER BY c DESC
            """
        ).fetchall()
        by_niche = connection.execute(
            """
            SELECT niche, COUNT(*) AS c FROM users
            WHERE is_member = 1 AND niche IS NOT NULL
            GROUP BY niche ORDER BY c DESC
            """
        ).fetchall()
        return {
            "total": total,
            "by_city": [dict(row) for row in by_city],
            "by_niche": [dict(row) for row in by_niche],
        }
