"""Quick test to verify database connection and seeded data."""
import asyncio
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from database import init_db, seed_data, get_pool


async def test():
    await init_db()
    print("OK - Tables created!")

    await seed_data()
    print("OK - Data seeded!")

    pool = await get_pool()

    cats = await pool.fetch("SELECT emoji, name FROM categories ORDER BY id")
    print(f"\nCategories ({len(cats)}):")
    for c in cats:
        print(f"  {c['name']}")

    prods = await pool.fetch("SELECT id, name, price FROM products ORDER BY id")
    print(f"\nProducts ({len(prods)}):")
    for p in prods:
        print(f"  #{p['id']} {p['name']} - Rs{p['price']}")

    print("\nOK - Everything works! Database is connected and ready.")


asyncio.run(test())
