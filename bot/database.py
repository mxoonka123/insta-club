import os
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

STATUS_NEW = "new"
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_REJECTED = "rejected"


def get_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def _column_names(connection: sqlite3.Connection, table: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return {row["name"] for row in rows}


def _migrate(connection: sqlite3.Connection) -> None:
    cols = _column_names(connection, "users")
    migrations = {
        "status": "ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'new'",
        "payment_claimed_at": "ALTER TABLE users ADD COLUMN payment_claimed_at TEXT",
        "admin_note": "ALTER TABLE users ADD COLUMN admin_note TEXT",
    }
    for column, sql in migrations.items():
        if column not in cols:
            connection.execute(sql)

    connection.execute(
        """
        UPDATE users
        SET status = 'active'
        WHERE is_member = 1 AND (status IS NULL OR status = '' OR status = 'new')
        """
    )
    connection.commit()


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
                status TEXT NOT NULL DEFAULT 'new',
                payment_claimed_at TEXT,
                admin_note TEXT,
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

            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                format TEXT NOT NULL,
                city TEXT NOT NULL,
                starts_at TEXT NOT NULL,
                topic TEXT NOT NULL,
                seats INTEGER,
                published INTEGER NOT NULL DEFAULT 0,
                reminder_day_sent INTEGER NOT NULL DEFAULT 0,
                reminder_hour_sent INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS meeting_rsvps (
                meeting_id INTEGER NOT NULL,
                telegram_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (meeting_id, telegram_id)
            );

            CREATE TABLE IF NOT EXISTS meeting_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                topic TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS app_flags (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '1',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        connection.commit()
        _migrate(connection)
        if os.getenv("SEED_DEMO", "").strip() in {"1", "true", "yes"}:
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
    until = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
    for telegram_id, username, full_name, city, niche, instagram, goal in demo:
        connection.execute(
            """
            INSERT INTO users (
                telegram_id, username, full_name, city, niche, instagram, goal,
                tariff, tariff_until, joined_at, referral_code, is_member, status, intro
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Business', ?, datetime('now'), ?, 1, 'active', ?)
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
            INSERT INTO users (telegram_id, username, referred_by, referral_code, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (telegram_id, username, referred_by, code, STATUS_NEW),
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
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET full_name = ?,
                city = ?,
                niche = ?,
                instagram = ?,
                goal = ?,
                tariff = 'START',
                tariff_until = NULL,
                joined_at = NULL,
                is_member = 0,
                status = ?,
                payment_claimed_at = NULL
            WHERE telegram_id = ?
            """,
            (full_name, city, niche, instagram, goal, STATUS_PENDING, telegram_id),
        )
        connection.commit()


def mark_payment_claimed(db_path: Path, telegram_id: int) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET payment_claimed_at = datetime('now'),
                status = ?
            WHERE telegram_id = ? AND status IN (?, ?)
            """,
            (STATUS_PENDING, telegram_id, STATUS_PENDING, STATUS_REJECTED),
        )
        connection.commit()
    return get_user(db_path, telegram_id)


def approve_member(db_path: Path, telegram_id: int, days: int = 30) -> dict[str, Any] | None:
    until = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET status = ?,
                is_member = 1,
                tariff = 'START',
                tariff_until = ?,
                joined_at = COALESCE(joined_at, datetime('now')),
                payment_claimed_at = COALESCE(payment_claimed_at, datetime('now'))
            WHERE telegram_id = ?
            """,
            (STATUS_ACTIVE, until, telegram_id),
        )
        connection.execute(
            """
            INSERT INTO payments (telegram_id, amount, description)
            VALUES (?, ?, ?)
            """,
            (telegram_id, "19 €", "Подтверждение оплаты START"),
        )
        connection.commit()
    return get_user(db_path, telegram_id)


def reject_member(db_path: Path, telegram_id: int, note: str | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET status = ?,
                is_member = 0,
                admin_note = ?
            WHERE telegram_id = ?
            """,
            (STATUS_REJECTED, note, telegram_id),
        )
        connection.commit()
    return get_user(db_path, telegram_id)


def revoke_member(db_path: Path, telegram_id: int, note: str | None = None) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET status = ?,
                is_member = 0,
                tariff_until = NULL,
                admin_note = ?
            WHERE telegram_id = ?
            """,
            (STATUS_REJECTED, note or "Доступ закрыт администратором", telegram_id),
        )
        connection.commit()
    return get_user(db_path, telegram_id)


def find_members(db_path: Path, query: str, limit: int = 15) -> list[dict[str, Any]]:
    raw = (query or "").strip().lstrip("@")
    digits = "".join(ch for ch in raw if ch.isdigit())
    found: list[dict[str, Any]] = []
    seen: set[int] = set()

    with get_connection(db_path) as connection:
        if digits:
            rows = connection.execute(
                """
                SELECT * FROM users
                WHERE telegram_id = ? OR CAST(telegram_id AS TEXT) = ?
                """,
                (int(digits), digits),
            ).fetchall()
            for row in rows:
                item = dict(row)
                seen.add(int(item["telegram_id"]))
                found.append(item)

        if raw:
            like = f"%{raw}%"
            rows = connection.execute(
                """
                SELECT * FROM users
                WHERE CAST(telegram_id AS TEXT) LIKE ?
                   OR IFNULL(full_name, '') LIKE ?
                   OR IFNULL(username, '') LIKE ?
                   OR IFNULL(niche, '') LIKE ?
                   OR IFNULL(city, '') LIKE ?
                ORDER BY is_member DESC, joined_at DESC
                LIMIT ?
                """,
                (f"%{digits or raw}%", like, like, like, like, limit),
            ).fetchall()
            for row in rows:
                item = dict(row)
                telegram_id = int(item["telegram_id"])
                if telegram_id not in seen:
                    seen.add(telegram_id)
                    found.append(item)

    return found[:limit]


def renew_subscription(db_path: Path, telegram_id: int, days: int = 30) -> dict[str, Any] | None:
    until = (datetime.utcnow() + timedelta(days=days)).strftime("%Y-%m-%d")
    with get_connection(db_path) as connection:
        connection.execute(
            """
            UPDATE users
            SET tariff_until = ?, status = ?, is_member = 1
            WHERE telegram_id = ?
            """,
            (until, STATUS_ACTIVE, telegram_id),
        )
        connection.execute(
            """
            INSERT INTO payments (telegram_id, amount, description)
            VALUES (?, ?, ?)
            """,
            (telegram_id, "19 €", "Продление START"),
        )
        connection.commit()
    return get_user(db_path, telegram_id)


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


def list_pending_applications(db_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE status = ? AND full_name IS NOT NULL
            ORDER BY
                CASE WHEN payment_claimed_at IS NULL THEN 1 ELSE 0 END,
                COALESCE(payment_claimed_at, created_at) DESC
            LIMIT ?
            """,
            (STATUS_PENDING, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def list_by_niche(db_path: Path, niche: str, limit: int = 20) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1 AND status = ? AND niche = ?
            ORDER BY joined_at DESC
            LIMIT ?
            """,
            (STATUS_ACTIVE, niche, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def list_new_members(db_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1 AND status = ?
            ORDER BY joined_at DESC
            LIMIT ?
            """,
            (STATUS_ACTIVE, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def search_members(db_path: Path, query: str, limit: int = 15) -> list[dict[str, Any]]:
    like = f"%{query.strip()}%"
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1 AND status = ? AND (
                full_name LIKE ? OR niche LIKE ? OR city LIKE ? OR goal LIKE ? OR intro LIKE ?
            )
            ORDER BY joined_at DESC
            LIMIT ?
            """,
            (STATUS_ACTIVE, like, like, like, like, like, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def count_referrals(db_path: Path, telegram_id: int) -> int:
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS c FROM users
            WHERE referred_by = ? AND is_member = 1 AND status = ?
            """,
            (telegram_id, STATUS_ACTIVE),
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
            "SELECT COUNT(*) AS c FROM users WHERE is_member = 1 AND status = ?",
            (STATUS_ACTIVE,),
        ).fetchone()["c"]
        pending = connection.execute(
            "SELECT COUNT(*) AS c FROM users WHERE status = ? AND full_name IS NOT NULL",
            (STATUS_PENDING,),
        ).fetchone()["c"]
        paid_claims = connection.execute(
            """
            SELECT COUNT(*) AS c FROM users
            WHERE status = ? AND payment_claimed_at IS NOT NULL
            """,
            (STATUS_PENDING,),
        ).fetchone()["c"]
        by_city = connection.execute(
            """
            SELECT city, COUNT(*) AS c FROM users
            WHERE is_member = 1 AND status = ? AND city IS NOT NULL
            GROUP BY city ORDER BY c DESC
            """,
            (STATUS_ACTIVE,),
        ).fetchall()
        by_niche = connection.execute(
            """
            SELECT niche, COUNT(*) AS c FROM users
            WHERE is_member = 1 AND status = ? AND niche IS NOT NULL
            GROUP BY niche ORDER BY c DESC
            """,
            (STATUS_ACTIVE,),
        ).fetchall()
        return {
            "total": total,
            "pending": pending,
            "paid_claims": paid_claims,
            "all_records": connection.execute(
                "SELECT COUNT(*) AS c FROM users"
            ).fetchone()["c"],
            "by_city": [dict(row) for row in by_city],
            "by_niche": [dict(row) for row in by_niche],
        }


def list_all_users(db_path: Path, limit: int = 30) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            ORDER BY
                CASE status
                    WHEN 'active' THEN 0
                    WHEN 'pending' THEN 1
                    ELSE 2
                END,
                COALESCE(joined_at, created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def list_active_members(db_path: Path) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM users
            WHERE is_member = 1 AND status = ?
            """,
            (STATUS_ACTIVE,),
        ).fetchall()
        return [dict(row) for row in rows]


def create_meeting(
    db_path: Path,
    *,
    format: str,
    city: str,
    starts_at: str,
    topic: str,
    seats: int | None,
) -> dict[str, Any]:
    with get_connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO meetings (format, city, starts_at, topic, seats, published)
            VALUES (?, ?, ?, ?, ?, 1)
            """,
            (format, city, starts_at, topic, seats),
        )
        meeting_id = cursor.lastrowid
        connection.commit()
        row = connection.execute(
            "SELECT * FROM meetings WHERE id = ?",
            (meeting_id,),
        ).fetchone()
        return dict(row)


def get_meeting(db_path: Path, meeting_id: int) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM meetings WHERE id = ?",
            (meeting_id,),
        ).fetchone()
        return dict(row) if row else None


def get_upcoming_meeting(db_path: Path) -> dict[str, Any] | None:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT * FROM meetings
            WHERE published = 1 AND starts_at >= ?
            ORDER BY starts_at ASC
            LIMIT 1
            """,
            (now,),
        ).fetchone()
        return dict(row) if row else None


def list_past_meetings(db_path: Path, limit: int = 10) -> list[dict[str, Any]]:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM meetings
            WHERE published = 1 AND starts_at < ?
            ORDER BY starts_at DESC
            LIMIT ?
            """,
            (now, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def list_upcoming_meetings(db_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM meetings
            WHERE published = 1 AND starts_at >= ?
            ORDER BY starts_at ASC
            LIMIT ?
            """,
            (now, limit),
        ).fetchall()
        return [dict(row) for row in rows]


def list_meetings_for_admin(db_path: Path, limit: int = 40) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT * FROM meetings
            ORDER BY starts_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]


def unpublish_meeting(db_path: Path, meeting_id: int) -> dict[str, Any] | None:
    with get_connection(db_path) as connection:
        connection.execute(
            "UPDATE meetings SET published = 0 WHERE id = ?",
            (meeting_id,),
        )
        connection.commit()
    return get_meeting(db_path, meeting_id)


def count_rsvps(db_path: Path, meeting_id: int) -> int:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS c FROM meeting_rsvps WHERE meeting_id = ?",
            (meeting_id,),
        ).fetchone()
        return int(row["c"])


def has_rsvp(db_path: Path, meeting_id: int, telegram_id: int) -> bool:
    with get_connection(db_path) as connection:
        row = connection.execute(
            """
            SELECT 1 FROM meeting_rsvps
            WHERE meeting_id = ? AND telegram_id = ?
            """,
            (meeting_id, telegram_id),
        ).fetchone()
        return row is not None


def list_rsvp_ids(db_path: Path, meeting_id: int) -> list[int]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT telegram_id FROM meeting_rsvps WHERE meeting_id = ?",
            (meeting_id,),
        ).fetchall()
        return [int(row["telegram_id"]) for row in rows]


def list_rsvp_users(db_path: Path, meeting_id: int) -> list[dict[str, Any]]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT
                r.telegram_id AS telegram_id,
                u.full_name AS full_name,
                u.username AS username,
                u.city AS city
            FROM meeting_rsvps r
            LEFT JOIN users u ON u.telegram_id = r.telegram_id
            WHERE r.meeting_id = ?
            ORDER BY r.created_at ASC
            """,
            (meeting_id,),
        ).fetchall()
        return [dict(row) for row in rows]


def rsvp_meeting(db_path: Path, meeting_id: int, telegram_id: int) -> str:
    meeting = get_meeting(db_path, meeting_id)
    if not meeting:
        return "missing"
    if has_rsvp(db_path, meeting_id, telegram_id):
        return "already"
    taken = count_rsvps(db_path, meeting_id)
    seats = meeting.get("seats")
    if seats is not None and taken >= int(seats):
        return "full"
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO meeting_rsvps (meeting_id, telegram_id)
            VALUES (?, ?)
            """,
            (meeting_id, telegram_id),
        )
        connection.commit()
    return "ok"


def cancel_rsvp(db_path: Path, meeting_id: int, telegram_id: int) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            "DELETE FROM meeting_rsvps WHERE meeting_id = ? AND telegram_id = ?",
            (meeting_id, telegram_id),
        )
        connection.commit()


def add_topic_suggestion(db_path: Path, telegram_id: int, topic: str) -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            "INSERT INTO meeting_topics (telegram_id, topic) VALUES (?, ?)",
            (telegram_id, topic),
        )
        connection.commit()


def meetings_for_reminder(db_path: Path, kind: str) -> list[dict[str, Any]]:
    now = datetime.utcnow()
    if kind == "day":
        start = now + timedelta(hours=22)
        end = now + timedelta(hours=26)
        flag = "reminder_day_sent"
    else:
        start = now + timedelta(minutes=90)
        end = now + timedelta(minutes=150)
        flag = "reminder_hour_sent"
    with get_connection(db_path) as connection:
        rows = connection.execute(
            f"""
            SELECT * FROM meetings
            WHERE published = 1
              AND {flag} = 0
              AND starts_at >= ?
              AND starts_at <= ?
            """,
            (
                start.strftime("%Y-%m-%dT%H:%M:%S"),
                end.strftime("%Y-%m-%dT%H:%M:%S"),
            ),
        ).fetchall()
        return [dict(row) for row in rows]


def mark_reminder_sent(db_path: Path, meeting_id: int, kind: str) -> None:
    column = "reminder_day_sent" if kind == "day" else "reminder_hour_sent"
    with get_connection(db_path) as connection:
        connection.execute(
            f"UPDATE meetings SET {column} = 1 WHERE id = ?",
            (meeting_id,),
        )
        connection.commit()


def has_app_flag(db_path: Path, key: str) -> bool:
    with get_connection(db_path) as connection:
        row = connection.execute(
            "SELECT 1 FROM app_flags WHERE key = ?",
            (key,),
        ).fetchone()
        return row is not None


def set_app_flag(db_path: Path, key: str, value: str = "1") -> None:
    with get_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO app_flags (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        connection.commit()


def list_started_telegram_ids(db_path: Path) -> list[int]:
    with get_connection(db_path) as connection:
        rows = connection.execute(
            "SELECT telegram_id FROM users ORDER BY created_at ASC"
        ).fetchall()
        return [int(row["telegram_id"]) for row in rows]
