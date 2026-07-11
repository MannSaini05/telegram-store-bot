"""
Async SQLite database manager for the Telegram Digital Store Bot.

Provides database initialisation, seed data insertion, and an async
context manager for obtaining database connections.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import aiosqlite

# Database file lives in the project root next to this module
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store.db")


async def init_db() -> None:
    """Create all tables if they do not already exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT,
                emoji       TEXT DEFAULT '📦',
                is_active   BOOLEAN DEFAULT 1,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER REFERENCES categories(id),
                name        TEXT NOT NULL,
                description TEXT,
                price       REAL NOT NULL,
                currency    TEXT DEFAULT 'INR',
                is_active   BOOLEAN DEFAULT 1,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS digital_keys (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id  INTEGER REFERENCES products(id),
                key_value   TEXT NOT NULL,
                is_sold     BOOLEAN DEFAULT 0,
                order_id    INTEGER,
                added_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sold_at     TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id                      INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id                 INTEGER NOT NULL,
                username                TEXT,
                first_name              TEXT,
                product_id              INTEGER REFERENCES products(id),
                quantity                INTEGER DEFAULT 1,
                total_price             REAL NOT NULL,
                status                  TEXT DEFAULT 'PENDING',
                payment_proof_file_id   TEXT,
                delivered_key           TEXT,
                created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        await db.commit()


async def seed_data() -> None:
    """
    Insert BGMI product catalog (Android + iOS) ONLY when the categories
    table is empty (first run).
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM categories")
        (count,) = await cursor.fetchone()
        if count > 0:
            return  # data already seeded

        # --- Categories (one per platform) ---
        categories = [
            ("📱 BGMI Android", "BGMI mod keys for Android devices", "📱"),
            ("🍎 BGMI iOS", "BGMI mod keys for iOS devices", "🍎"),
        ]
        await db.executemany(
            "INSERT INTO categories (name, description, emoji) VALUES (?, ?, ?)",
            categories,
        )

        # --- Products ---
        # Category 1 = Android, Category 2 = iOS
        # Same 3 mods (MARS Loader, ZTRAX, King Mod) with same tiers on both platforms

        products = [
            # ── Android (category_id = 1) ──────────────────────────────

            # MARS Loader — 4 tiers
            (1, "MARS Loader — 1 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Day access",    80.0),
            (1, "MARS Loader — 3 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 3 Day access",   200.0),
            (1, "MARS Loader — 1 Week",  "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Week access",  320.0),
            (1, "MARS Loader — 1 Month", "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Month access", 650.0),

            # ZTRAX — 4 tiers
            (1, "ZTRAX — 1 Day",    "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Day access",      140.0),
            (1, "ZTRAX — 1 Week",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Week access",     400.0),
            (1, "ZTRAX — 1 Month",  "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Month access",    999.0),
            (1, "ZTRAX — Season",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • Full Season access", 1400.0),

            # King Mod — 3 tiers
            (1, "King Mod — 1 Day",   "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Day access",   200.0),
            (1, "King Mod — 1 Week",  "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Week access",  700.0),
            (1, "King Mod — 1 Month", "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Month access", 1800.0),

            # ── iOS (category_id = 2) ──────────────────────────────────

            # MARS Loader — 4 tiers
            (2, "MARS Loader — 1 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Day access",    80.0),
            (2, "MARS Loader — 3 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 3 Day access",   200.0),
            (2, "MARS Loader — 1 Week",  "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Week access",  320.0),
            (2, "MARS Loader — 1 Month", "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Month access", 650.0),

            # ZTRAX — 4 tiers
            (2, "ZTRAX — 1 Day",    "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Day access",      140.0),
            (2, "ZTRAX — 1 Week",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Week access",     400.0),
            (2, "ZTRAX — 1 Month",  "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Month access",    999.0),
            (2, "ZTRAX — Season",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • Full Season access", 1400.0),

            # King Mod — 3 tiers
            (2, "King Mod — 1 Day",   "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Day access",   200.0),
            (2, "King Mod — 1 Week",  "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Week access",  700.0),
            (2, "King Mod — 1 Month", "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Month access", 1800.0),
        ]
        await db.executemany(
            "INSERT INTO products (category_id, name, description, price) VALUES (?, ?, ?, ?)",
            products,
        )

        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Async context manager that yields an aiosqlite connection with
    row_factory set to aiosqlite.Row for dict-like access.

    Usage::

        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM categories")
            rows = await cursor.fetchall()
    """
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
