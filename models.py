"""
Async query / mutation functions for the Telegram Digital Store Bot.

Uses asyncpg with PostgreSQL. All functions use the shared connection pool.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database import get_pool


# ── Helper ──────────────────────────────────────────────────────────────────

def _record_to_dict(record) -> Dict[str, Any]:
    """Convert an asyncpg Record to a plain dict."""
    return dict(record) if record else {}


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

async def get_categories() -> List[Dict[str, Any]]:
    """Return all active categories."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM categories WHERE is_active = TRUE ORDER BY id"
    )
    return [dict(r) for r in rows]


async def get_category(category_id: int) -> Optional[Dict[str, Any]]:
    """Return a single category by id, or None."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM categories WHERE id = $1", category_id
    )
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

async def get_products_by_category(category_id: int) -> List[Dict[str, Any]]:
    """Return all active products in a category."""
    pool = await get_pool()
    rows = await pool.fetch(
        "SELECT * FROM products WHERE category_id = $1 AND is_active = TRUE ORDER BY id",
        category_id,
    )
    return [dict(r) for r in rows]


async def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    """Return a single product by id, or None."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM products WHERE id = $1", product_id
    )
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Digital Keys / Stock
# ---------------------------------------------------------------------------

async def get_stock_count(product_id: int) -> int:
    """Return the number of unsold keys available for a product."""
    pool = await get_pool()
    count = await pool.fetchval(
        "SELECT COUNT(*) FROM digital_keys WHERE product_id = $1 AND is_sold = FALSE",
        product_id,
    )
    return count or 0


async def get_available_key(product_id: int) -> Optional[Dict[str, Any]]:
    """Return the first unsold key for a product, or None."""
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM digital_keys WHERE product_id = $1 AND is_sold = FALSE ORDER BY id LIMIT 1",
        product_id,
    )
    return dict(row) if row else None


async def mark_key_sold(key_id: int, order_id: int) -> None:
    """Mark a digital key as sold and record the timestamp."""
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    await pool.execute(
        "UPDATE digital_keys SET is_sold = TRUE, order_id = $1, sold_at = $2 WHERE id = $3",
        order_id, now, key_id,
    )


async def add_digital_keys(product_id: int, keys_list: List[str]) -> int:
    """Bulk-insert digital keys for a product. Return the count added."""
    pool = await get_pool()
    clean_keys = [(product_id, k.strip()) for k in keys_list if k.strip()]
    async with pool.acquire() as conn:
        await conn.executemany(
            "INSERT INTO digital_keys (product_id, key_value) VALUES ($1, $2)",
            clean_keys,
        )
    return len(clean_keys)


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

async def create_order(
    user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    product_id: int,
    quantity: int,
    total_price: float,
    payment_proof_file_id: Optional[str],
) -> int:
    """Create a new order and return its id."""
    pool = await get_pool()
    order_id = await pool.fetchval(
        """
        INSERT INTO orders
            (user_id, username, first_name, product_id, quantity,
             total_price, payment_proof_file_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING id
        """,
        user_id, username, first_name, product_id, quantity,
        total_price, payment_proof_file_id,
    )
    return order_id


async def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    """Return a single order with the product name joined in."""
    pool = await get_pool()
    row = await pool.fetchrow(
        """
        SELECT o.*, p.name AS product_name
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        WHERE o.id = $1
        """,
        order_id,
    )
    return dict(row) if row else None


async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """Return all orders for a user with product names, newest first."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT o.*, p.name AS product_name
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        WHERE o.user_id = $1
        ORDER BY o.created_at DESC
        """,
        user_id,
    )
    return [dict(r) for r in rows]


async def update_order_status(order_id: int, status: str) -> None:
    """Update the status of an order and refresh updated_at."""
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    await pool.execute(
        "UPDATE orders SET status = $1, updated_at = $2 WHERE id = $3",
        status, now, order_id,
    )


async def set_order_delivered_key(order_id: int, key_value: str) -> None:
    """Record the delivered key on the order."""
    pool = await get_pool()
    now = datetime.now(timezone.utc)
    await pool.execute(
        "UPDATE orders SET delivered_key = $1, updated_at = $2 WHERE id = $3",
        key_value, now, order_id,
    )


async def get_pending_orders() -> List[Dict[str, Any]]:
    """Return all orders with PENDING status, with product names."""
    pool = await get_pool()
    rows = await pool.fetch(
        """
        SELECT o.*, p.name AS product_name
        FROM orders o
        LEFT JOIN products p ON o.product_id = p.id
        WHERE o.status = 'PENDING'
        ORDER BY o.created_at ASC
        """,
    )
    return [dict(r) for r in rows]


async def get_order_stats() -> Dict[str, Any]:
    """
    Return aggregate order statistics:
    total_orders, pending_count, approved_count, delivered_count, total_revenue.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        total_orders = await conn.fetchval("SELECT COUNT(*) FROM orders") or 0
        pending_count = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'PENDING'") or 0
        approved_count = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'APPROVED'") or 0
        delivered_count = await conn.fetchval("SELECT COUNT(*) FROM orders WHERE status = 'DELIVERED'") or 0
        total_revenue = await conn.fetchval("SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE status = 'DELIVERED'") or 0

    return {
        "total_orders": total_orders,
        "pending_count": pending_count,
        "approved_count": approved_count,
        "delivered_count": delivered_count,
        "total_revenue": float(total_revenue),
    }


# ---------------------------------------------------------------------------
# Admin helpers – add new products / categories
# ---------------------------------------------------------------------------

async def add_product(
    category_id: int,
    name: str,
    description: str,
    price: float,
) -> int:
    """Insert a new product and return its id."""
    pool = await get_pool()
    product_id = await pool.fetchval(
        """
        INSERT INTO products (category_id, name, description, price)
        VALUES ($1, $2, $3, $4)
        RETURNING id
        """,
        category_id, name, description, price,
    )
    return product_id


async def add_category(name: str, description: str, emoji: str) -> int:
    """Insert a new category and return its id."""
    pool = await get_pool()
    category_id = await pool.fetchval(
        """
        INSERT INTO categories (name, description, emoji)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        name, description, emoji,
    )
    return category_id
