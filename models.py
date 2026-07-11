"""
Async query / mutation functions for the Telegram Digital Store Bot.

Every function opens its own connection via ``get_db()`` so callers
never need to manage connections themselves.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database import get_db


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

async def get_categories() -> List[Dict[str, Any]]:
    """Return all active categories."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY id"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_category(category_id: int) -> Optional[Dict[str, Any]]:
    """Return a single category by id, or None."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM categories WHERE id = ?", (category_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

async def get_products_by_category(category_id: int) -> List[Dict[str, Any]]:
    """Return all active products in a category."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE category_id = ? AND is_active = 1 ORDER BY id",
            (category_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    """Return a single product by id, or None."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM products WHERE id = ?", (product_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Digital Keys / Stock
# ---------------------------------------------------------------------------

async def get_stock_count(product_id: int) -> int:
    """Return the number of unsold keys available for a product."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM digital_keys WHERE product_id = ? AND is_sold = 0",
            (product_id,),
        )
        (count,) = await cursor.fetchone()
        return count


async def get_available_key(product_id: int) -> Optional[Dict[str, Any]]:
    """Return the first unsold key for a product, or None."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT * FROM digital_keys WHERE product_id = ? AND is_sold = 0 ORDER BY id LIMIT 1",
            (product_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def mark_key_sold(key_id: int, order_id: int) -> None:
    """Mark a digital key as sold and record the timestamp."""
    async with get_db() as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE digital_keys SET is_sold = 1, order_id = ?, sold_at = ? WHERE id = ?",
            (order_id, now, key_id),
        )
        await db.commit()


async def add_digital_keys(product_id: int, keys_list: List[str]) -> int:
    """Bulk-insert digital keys for a product. Return the count added."""
    async with get_db() as db:
        rows = [(product_id, key.strip()) for key in keys_list if key.strip()]
        await db.executemany(
            "INSERT INTO digital_keys (product_id, key_value) VALUES (?, ?)",
            rows,
        )
        await db.commit()
        return len(rows)


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
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO orders
                (user_id, username, first_name, product_id, quantity,
                 total_price, payment_proof_file_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, first_name, product_id, quantity,
             total_price, payment_proof_file_id),
        )
        await db.commit()
        return cursor.lastrowid


async def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    """Return a single order with the product name joined in."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT o.*, p.name AS product_name
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.id = ?
            """,
            (order_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
    """Return all orders for a user with product names, newest first."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT o.*, p.name AS product_name
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.user_id = ?
            ORDER BY o.created_at DESC
            """,
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def update_order_status(order_id: int, status: str) -> None:
    """Update the status of an order and refresh updated_at."""
    async with get_db() as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, order_id),
        )
        await db.commit()


async def set_order_delivered_key(order_id: int, key_value: str) -> None:
    """Record the delivered key on the order."""
    async with get_db() as db:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            "UPDATE orders SET delivered_key = ?, updated_at = ? WHERE id = ?",
            (key_value, now, order_id),
        )
        await db.commit()


async def get_pending_orders() -> List[Dict[str, Any]]:
    """Return all orders with PENDING status, with product names."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT o.*, p.name AS product_name
            FROM orders o
            LEFT JOIN products p ON o.product_id = p.id
            WHERE o.status = 'PENDING'
            ORDER BY o.created_at ASC
            """,
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_order_stats() -> Dict[str, Any]:
    """
    Return aggregate order statistics:
    total_orders, pending_count, approved_count, delivered_count, total_revenue.
    Revenue is calculated from delivered orders only.
    """
    async with get_db() as db:
        cursor = await db.execute("SELECT COUNT(*) FROM orders")
        (total_orders,) = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'PENDING'"
        )
        (pending_count,) = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'APPROVED'"
        )
        (approved_count,) = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'DELIVERED'"
        )
        (delivered_count,) = await cursor.fetchone()

        cursor = await db.execute(
            "SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE status = 'DELIVERED'"
        )
        (total_revenue,) = await cursor.fetchone()

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
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO products (category_id, name, description, price)
            VALUES (?, ?, ?, ?)
            """,
            (category_id, name, description, price),
        )
        await db.commit()
        return cursor.lastrowid


async def add_category(name: str, description: str, emoji: str) -> int:
    """Insert a new category and return its id."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            INSERT INTO categories (name, description, emoji)
            VALUES (?, ?, ?)
            """,
            (name, description, emoji),
        )
        await db.commit()
        return cursor.lastrowid
