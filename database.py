"""
Async PostgreSQL database manager for the Telegram Digital Store Bot.

Uses asyncpg with a connection pool for Supabase/Neon PostgreSQL.
"""

import asyncpg
from config import DATABASE_URL

# Global connection pool
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return _pool


async def init_db() -> None:
    """Create all tables if they do not already exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id          SERIAL PRIMARY KEY,
                name        TEXT NOT NULL,
                description TEXT,
                emoji       TEXT DEFAULT '📦',
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS products (
                id          SERIAL PRIMARY KEY,
                category_id INTEGER REFERENCES categories(id),
                name        TEXT NOT NULL,
                description TEXT,
                price       REAL NOT NULL,
                currency    TEXT DEFAULT 'INR',
                is_active   BOOLEAN DEFAULT TRUE,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS digital_keys (
                id          SERIAL PRIMARY KEY,
                product_id  INTEGER REFERENCES products(id),
                key_value   TEXT NOT NULL,
                is_sold     BOOLEAN DEFAULT FALSE,
                order_id    INTEGER,
                added_at    TIMESTAMP DEFAULT NOW(),
                sold_at     TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS orders (
                id                      SERIAL PRIMARY KEY,
                user_id                 BIGINT NOT NULL,
                username                TEXT,
                first_name              TEXT,
                product_id              INTEGER REFERENCES products(id),
                quantity                INTEGER DEFAULT 1,
                total_price             REAL NOT NULL,
                status                  TEXT DEFAULT 'PENDING',
                payment_proof_file_id   TEXT,
                delivered_key           TEXT,
                created_at              TIMESTAMP DEFAULT NOW(),
                updated_at              TIMESTAMP DEFAULT NOW()
            );
        """)


async def seed_data() -> None:
    """
    Insert BGMI product catalog (Android + iOS) ONLY when the categories
    table is empty (first run).
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM categories")
        if count > 0:
            return  # data already seeded

        # --- Categories (one per platform) ---
        await conn.executemany(
            "INSERT INTO categories (name, description, emoji) VALUES ($1, $2, $3)",
            [
                ("📱 BGMI Android", "BGMI mod keys for Android devices", "📱"),
                ("🍎 BGMI iOS", "BGMI mod keys for iOS devices", "🍎"),
            ],
        )

        # --- Products ---
        # Category 1 = Android, Category 2 = iOS
        products = [
            # ── Android (category_id = 1) ──────────────────────────────
            (1, "MARS Loader — 1 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Day access",    80.0),
            (1, "MARS Loader — 3 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 3 Day access",   200.0),
            (1, "MARS Loader — 1 Week",  "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Week access",  320.0),
            (1, "MARS Loader — 1 Month", "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Month access", 650.0),
            (1, "ZTRAX — 1 Day",    "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Day access",      140.0),
            (1, "ZTRAX — 1 Week",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Week access",     400.0),
            (1, "ZTRAX — 1 Month",  "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Month access",    999.0),
            (1, "ZTRAX — Season",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • Full Season access", 1400.0),
            (1, "King Mod — 1 Day",   "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Day access",   200.0),
            (1, "King Mod — 1 Week",  "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Week access",  700.0),
            (1, "King Mod — 1 Month", "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Month access", 1800.0),

            # ── iOS (category_id = 2) ──────────────────────────────────
            (2, "MARS Loader — 1 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Day access",    80.0),
            (2, "MARS Loader — 3 Day",   "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 3 Day access",   200.0),
            (2, "MARS Loader — 1 Week",  "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Week access",  320.0),
            (2, "MARS Loader — 1 Month", "Cheap ESP + Aimbot • Anti-cheat bypass • Auto-update on patch • Full ESP suite • 1 Month access", 650.0),
            (2, "ZTRAX — 1 Day",    "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Day access",      140.0),
            (2, "ZTRAX — 1 Week",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Week access",     400.0),
            (2, "ZTRAX — 1 Month",  "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • 1 Month access",    999.0),
            (2, "ZTRAX — Season",   "Bypass with ESP + Aimbot • Touch simulation aimbot • Recoil control • Bullet prediction • Full Season access", 1400.0),
            (2, "King Mod — 1 Day",   "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Day access",   200.0),
            (2, "King Mod — 1 Week",  "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Week access",  700.0),
            (2, "King Mod — 1 Month", "Premium Skins + Kill Message + ESP + Aimbot • Custom kill messages • Premium weapon skins • 360° ESP • 1 Month access", 1800.0),
        ]
        await conn.executemany(
            "INSERT INTO products (category_id, name, description, price) VALUES ($1, $2, $3, $4)",
            products,
        )
