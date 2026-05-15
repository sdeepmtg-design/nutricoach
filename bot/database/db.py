import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import aiosqlite

from bot.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    created_at TEXT NOT NULL,
    onboarding_done INTEGER DEFAULT 0,
    gender TEXT,
    age INTEGER,
    height_cm REAL,
    weight_kg REAL,
    activity TEXT,
    goal TEXT,
    target_weight_kg REAL,
    daily_calories INTEGER,
    daily_protein_g INTEGER,
    daily_fat_g INTEGER,
    daily_carbs_g INTEGER,
    pro_until TEXT,
    program TEXT DEFAULT 'maintain'
);

CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    meal_type TEXT NOT NULL,
    description TEXT NOT NULL,
    calories INTEGER DEFAULT 0,
    protein_g REAL DEFAULT 0,
    fat_g REAL DEFAULT 0,
    carbs_g REAL DEFAULT 0,
    confidence TEXT,
    tips_good TEXT,
    tips_limit TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS weight_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight_kg REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS usage_daily (
    user_id INTEGER NOT NULL,
    usage_date TEXT NOT NULL,
    photos_count INTEGER DEFAULT 0,
    ai_messages_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, usage_date)
);

CREATE TABLE IF NOT EXISTS usage_monthly (
    user_id INTEGER NOT NULL,
    usage_month TEXT NOT NULL,
    photos_count INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, usage_month)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    plan TEXT NOT NULL,
    stars_amount INTEGER NOT NULL,
    charge_id TEXT,
    created_at TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or settings.database_path

    async def connect(self) -> aiosqlite.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = await aiosqlite.connect(self.path)
        conn.row_factory = aiosqlite.Row
        await conn.executescript(SCHEMA)
        await conn.commit()
        return conn

    async def ensure_user(
        self,
        user_id: int,
        username: str | None,
        first_name: str | None,
    ) -> dict[str, Any]:
        async with await self.connect() as conn:
            row = await (
                await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            ).fetchone()
            now = datetime.utcnow().isoformat()
            if row is None:
                await conn.execute(
                    """INSERT INTO users (user_id, username, first_name, created_at)
                       VALUES (?, ?, ?, ?)""",
                    (user_id, username, first_name, now),
                )
                await conn.commit()
                row = await (
                    await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                ).fetchone()
            return dict(row)

    async def update_user(self, user_id: int, **fields: Any) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        vals = list(fields.values()) + [user_id]
        async with await self.connect() as conn:
            await conn.execute(f"UPDATE users SET {cols} WHERE user_id = ?", vals)
            await conn.commit()

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        async with await self.connect() as conn:
            row = await (
                await conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            ).fetchone()
            return dict(row) if row else None

    def is_pro(self, user: dict[str, Any]) -> bool:
        until = user.get("pro_until")
        if not until:
            return False
        return datetime.fromisoformat(until) > datetime.utcnow()

    async def activate_pro(self, user_id: int, days: int) -> None:
        user = await self.get_user(user_id)
        base = datetime.utcnow()
        if user and user.get("pro_until"):
            current = datetime.fromisoformat(user["pro_until"])
            if current > base:
                base = current
        new_until = (base + timedelta(days=days)).isoformat()
        await self.update_user(user_id, pro_until=new_until)

    async def add_meal(
        self,
        user_id: int,
        meal_type: str,
        description: str,
        calories: int,
        protein_g: float,
        fat_g: float,
        carbs_g: float,
        confidence: str | None = None,
        tips_good: str | None = None,
        tips_limit: str | None = None,
    ) -> int:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as conn:
            cur = await conn.execute(
                """INSERT INTO meals
                   (user_id, meal_type, description, calories, protein_g, fat_g, carbs_g,
                    confidence, tips_good, tips_limit, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    meal_type,
                    description,
                    calories,
                    protein_g,
                    fat_g,
                    carbs_g,
                    confidence,
                    tips_good,
                    tips_limit,
                    now,
                ),
            )
            await conn.commit()
            return cur.lastrowid or 0

    async def get_meals_today(self, user_id: int) -> list[dict[str, Any]]:
        today = date.today().isoformat()
        async with await self.connect() as conn:
            rows = await (
                await conn.execute(
                    """SELECT * FROM meals
                       WHERE user_id = ? AND created_at LIKE ?
                       ORDER BY created_at""",
                    (user_id, f"{today}%"),
                )
            ).fetchall()
            return [dict(r) for r in rows]

    async def get_meals_week(self, user_id: int) -> list[dict[str, Any]]:
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        async with await self.connect() as conn:
            rows = await (
                await conn.execute(
                    """SELECT * FROM meals
                       WHERE user_id = ? AND created_at >= ?
                       ORDER BY created_at""",
                    (user_id, week_ago),
                )
            ).fetchall()
            return [dict(r) for r in rows]

    async def log_weight(self, user_id: int, weight_kg: float) -> None:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as conn:
            await conn.execute(
                "INSERT INTO weight_log (user_id, weight_kg, created_at) VALUES (?, ?, ?)",
                (user_id, weight_kg, now),
            )
            await conn.execute(
                "UPDATE users SET weight_kg = ? WHERE user_id = ?",
                (weight_kg, user_id),
            )
            await conn.commit()

    async def get_weight_history(self, user_id: int, limit: int = 14) -> list[dict[str, Any]]:
        async with await self.connect() as conn:
            rows = await (
                await conn.execute(
                    """SELECT * FROM weight_log
                       WHERE user_id = ?
                       ORDER BY created_at DESC LIMIT ?""",
                    (user_id, limit),
                )
            ).fetchall()
            return [dict(r) for r in reversed(rows)]

    async def increment_usage(self, user_id: int, photos: int = 0, ai: int = 0) -> None:
        today = date.today().isoformat()
        month = today[:7]
        async with await self.connect() as conn:
            await conn.execute(
                """INSERT INTO usage_daily (user_id, usage_date, photos_count, ai_messages_count)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id, usage_date) DO UPDATE SET
                     photos_count = photos_count + excluded.photos_count,
                     ai_messages_count = ai_messages_count + excluded.ai_messages_count""",
                (user_id, today, photos, ai),
            )
            if photos:
                await conn.execute(
                    """INSERT INTO usage_monthly (user_id, usage_month, photos_count)
                       VALUES (?, ?, ?)
                       ON CONFLICT(user_id, usage_month) DO UPDATE SET
                         photos_count = photos_count + excluded.photos_count""",
                    (user_id, month, photos),
                )
            await conn.commit()

    async def get_usage(self, user_id: int) -> dict[str, int]:
        today = date.today().isoformat()
        month = today[:7]
        async with await self.connect() as conn:
            daily = await (
                await conn.execute(
                    "SELECT * FROM usage_daily WHERE user_id = ? AND usage_date = ?",
                    (user_id, today),
                )
            ).fetchone()
            monthly = await (
                await conn.execute(
                    "SELECT * FROM usage_monthly WHERE user_id = ? AND usage_month = ?",
                    (user_id, month),
                )
            ).fetchone()
        d = dict(daily) if daily else {}
        m = dict(monthly) if monthly else {}
        return {
            "photos_today": d.get("photos_count", 0),
            "ai_today": d.get("ai_messages_count", 0),
            "photos_month": m.get("photos_count", 0),
        }

    async def record_payment(
        self, user_id: int, plan: str, stars: int, charge_id: str | None
    ) -> None:
        now = datetime.utcnow().isoformat()
        async with await self.connect() as conn:
            await conn.execute(
                """INSERT INTO payments (user_id, plan, stars_amount, charge_id, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, plan, stars, charge_id, now),
            )
            await conn.commit()


db = Database()
