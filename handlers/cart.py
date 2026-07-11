"""Cart / purchase-flow handlers — payment details and confirmation."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CURRENCY_SYMBOL, UPI_ID, BANK_NAME, BANK_ACCOUNT, BANK_IFSC
import models


async def buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `buy_{id}` callback — show payment instructions."""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_", 1)[1])
    product = await models.get_product(product_id)

    if not product:
        await query.edit_message_text(
            "⚠️ Product not found.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]]
            ),
        )
        return

    # Verify stock before showing payment details
    stock = await models.get_stock_count(product_id)
    if stock <= 0:
        await query.edit_message_text(
            "⚠️ Sorry, this product is currently <b>out of stock</b>.\n"
            "Please check back later!",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data=f"prod_{product_id}")]]
            ),
        )
        return

    context.user_data["pending_product_id"] = product_id

    text = (
        "💳 <b>Payment Details</b>\n"
        "\n"
        f"📦 Product: <b>{product['name']}</b>\n"
        f"💰 Amount: <b>{CURRENCY_SYMBOL}{product['price']}</b>\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "🏦 <b>UPI Payment:</b>\n"
        f"   UPI ID: <code>{UPI_ID}</code>\n"
        "\n"
        "🏦 <b>Bank Transfer:</b>\n"
        f"   Bank: {BANK_NAME}\n"
        f"   A/C: <code>{BANK_ACCOUNT}</code>\n"
        f"   IFSC: <code>{BANK_IFSC}</code>\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "✅ After payment, tap <b>'I've Paid'</b> and\n"
        "send your payment screenshot."
    )

    keyboard = [
        [InlineKeyboardButton("✅ I've Paid", callback_data=f"confirm_buy_{product_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="menu_main")],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def confirm_buy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `confirm_buy_{id}` callback — ask user for payment screenshot."""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("confirm_buy_", 1)[1])
    product = await models.get_product(product_id)

    if not product:
        await query.edit_message_text(
            "⚠️ Product not found.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]]
            ),
        )
        return

    context.user_data["awaiting_proof"] = True
    context.user_data["pending_product_id"] = product_id

    text = (
        "📸 <b>Send Payment Proof</b>\n"
        "\n"
        f"📦 Product: <b>{product['name']}</b>\n"
        f"💰 Amount: <b>{CURRENCY_SYMBOL}{product['price']}</b>\n"
        "\n"
        "Please send your payment screenshot or receipt now.\n"
        "Supported formats: 📷 photo or 📄 PDF document."
    )

    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="menu_main")]]

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )
