"""Payment proof handler — processes photo / document uploads as payment proof."""

from datetime import datetime, timezone, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_CHAT_ID, CURRENCY_SYMBOL
import models

# IST offset for timestamp display
_IST = timezone(timedelta(hours=5, minutes=30))


async def payment_proof_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photo or document messages as payment proof.

    Only processes the message if the user is in the 'awaiting_proof' state.
    Supports both photo uploads and document attachments (PDF receipts, etc.).
    """
    if not context.user_data.get("awaiting_proof"):
        return  # Not awaiting proof — ignore silently

    # Determine file_id from photo or document
    if update.message.photo:
        file_id = update.message.photo[-1].file_id  # Highest resolution
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        return  # Unsupported attachment type

    product_id = context.user_data.get("pending_product_id")
    if not product_id:
        context.user_data.pop("awaiting_proof", None)
        await update.message.reply_text(
            "⚠️ Something went wrong. Please start a new purchase.",
            parse_mode="HTML",
        )
        return

    product = await models.get_product(product_id)
    if not product:
        context.user_data.pop("awaiting_proof", None)
        context.user_data.pop("pending_product_id", None)
        await update.message.reply_text(
            "⚠️ Product not found. Please try again.",
            parse_mode="HTML",
        )
        return

    user = update.effective_user
    username = user.username or "N/A"
    first_name = user.first_name or "Customer"

    # Create order
    order_id = await models.create_order(
        user_id=user.id,
        username=username,
        first_name=first_name,
        product_id=product_id,
        quantity=1,
        total_price=product["price"],
        payment_proof_file_id=file_id,
    )

    # Clear state
    context.user_data.pop("awaiting_proof", None)
    context.user_data.pop("pending_product_id", None)

    # ── Send confirmation to customer ──
    customer_text = (
        "✅ <b>Order Placed Successfully!</b>\n"
        "\n"
        f"🆔 Order ID: <b>#{order_id}</b>\n"
        f"📦 Product: <b>{product['name']}</b>\n"
        f"💰 Amount: <b>{CURRENCY_SYMBOL}{product['price']}</b>\n"
        f"📋 Status: ⏳ <i>Pending Verification</i>\n"
        "\n"
        "You'll be notified once your payment is verified! 🔔"
    )
    keyboard = [[InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]]
    await update.message.reply_text(
        customer_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    # ── Send notification to admin ──
    now = datetime.now(_IST).strftime("%d %b %Y, %I:%M %p IST")
    admin_text = (
        f"🔔 <b>NEW ORDER #{order_id}</b>\n"
        "\n"
        f"👤 Customer: @{username} ({first_name})\n"
        f"🆔 User ID: <code>{user.id}</code>\n"
        f"📦 Product: <b>{product['name']}</b>\n"
        f"💰 Amount: <b>{CURRENCY_SYMBOL}{product['price']}</b>\n"
        f"📅 Time: {now}\n"
        "\n"
        "📸 Payment proof attached below ⬇️"
    )
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=admin_text,
        parse_mode="HTML",
    )

    # Send the payment proof to admin
    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=file_id)
    else:
        await context.bot.send_document(chat_id=ADMIN_CHAT_ID, document=file_id)

    # Send action buttons to admin
    action_keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order_id}"),
        ]
    ]
    await context.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text=f"<b>Actions for Order #{order_id}:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(action_keyboard),
    )
