"""
Telegram Digital Store Bot — Main Entry Point

Initializes the database, registers all handlers, and starts polling.
"""

import asyncio
import logging
import sys
import os

# Ensure project root is on the path so handler imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, ADMIN_CHAT_ID
from database import init_db, seed_data

# Handlers
from handlers.start import start_command, main_menu_callback, support_callback
from handlers.browse import browse_callback, platform_callback, category_callback, product_callback
from handlers.cart import buy_callback, confirm_buy_callback
from handlers.payment import payment_proof_handler
from handlers.orders import my_orders_callback, order_detail_callback, my_orders_command
from handlers.admin import (
    approve_callback,
    reject_callback,
    sendkey_command,
    addkeys_command,
    addkeys_text_handler,
    addproduct_command,
    addcategory_command,
    stats_command,
    pending_orders_command,
)

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Silence noisy httpx logs from python-telegram-bot
logging.getLogger("httpx").setLevel(logging.WARNING)


# ── Post-init hook (runs after app.initialize) ──────────────────────────────

async def post_init(application: Application) -> None:
    """Initialize the database and seed example data on first run."""
    await init_db()
    await seed_data()
    logger.info("Database initialized and seeded.")
    logger.info(f"Admin chat ID: {ADMIN_CHAT_ID}")
    logger.info("Bot is starting...")


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    """Build the application, register handlers, and run the bot."""

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Command handlers ────────────────────────────────────────────────
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("myorders", my_orders_command))
    application.add_handler(CommandHandler("sendkey", sendkey_command))
    application.add_handler(CommandHandler("addkeys", addkeys_command))
    application.add_handler(CommandHandler("addproduct", addproduct_command))
    application.add_handler(CommandHandler("addcategory", addcategory_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("orders", pending_orders_command))

    # ── Callback query handlers (inline button presses) ─────────────────
    # Order matters: more specific patterns first.

    # Navigation
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern=r"^menu_main$"))
    application.add_handler(CallbackQueryHandler(support_callback, pattern=r"^support$"))
    application.add_handler(CallbackQueryHandler(browse_callback, pattern=r"^browse$"))

    # Browsing
    application.add_handler(CallbackQueryHandler(platform_callback, pattern=r"^platform_(android|ios)$"))
    application.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat_\d+$"))
    application.add_handler(CallbackQueryHandler(product_callback, pattern=r"^prod_\d+$"))

    # Purchase flow
    application.add_handler(CallbackQueryHandler(buy_callback, pattern=r"^buy_\d+$"))
    application.add_handler(CallbackQueryHandler(confirm_buy_callback, pattern=r"^confirm_buy_\d+$"))

    # Orders
    application.add_handler(CallbackQueryHandler(my_orders_callback, pattern=r"^myorders$"))
    application.add_handler(CallbackQueryHandler(order_detail_callback, pattern=r"^order_\d+$"))

    # Admin actions
    application.add_handler(CallbackQueryHandler(approve_callback, pattern=r"^approve_\d+$"))
    application.add_handler(CallbackQueryHandler(reject_callback, pattern=r"^reject_\d+$"))

    # ── Message handlers ────────────────────────────────────────────────
    # Payment proof (photos & documents) — must come before the text handler
    application.add_handler(
        MessageHandler(filters.PHOTO | filters.Document.ALL, payment_proof_handler)
    )

    # Admin key-adding text handler (text from admin when in add-keys mode)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, addkeys_text_handler)
    )

    # ── Start polling ───────────────────────────────────────────────────
    logger.info("🚀 Bot started! Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
