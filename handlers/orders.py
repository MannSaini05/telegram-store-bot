"""Order listing and detail handlers for customers."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CURRENCY_SYMBOL
import models

# Status → emoji mapping
_STATUS_EMOJI = {
    "PENDING": "⏳",
    "APPROVED": "✅",
    "DELIVERED": "📬",
    "REJECTED": "❌",
    "CANCELLED": "🚫",
}


def _status_icon(status: str) -> str:
    """Return the emoji for a given order status."""
    return _STATUS_EMOJI.get(status.upper(), "❓")


async def _show_orders(update: Update, context: ContextTypes.DEFAULT_TYPE, *, edit: bool) -> None:
    """Shared implementation for displaying a user's orders.

    Args:
        edit: If True, edit the existing message (callback). If False, send a new message (command).
    """
    user_id = update.effective_user.id
    orders = await models.get_user_orders(user_id)

    if not orders:
        text = (
            "📦 <b>My Orders</b>\n"
            "\n"
            "You haven't placed any orders yet.\n"
            "Browse our catalog to get started! 🛒"
        )
        keyboard = [
            [InlineKeyboardButton("🛒 Browse Products", callback_data="browse")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")],
        ]
    else:
        lines = ["📦 <b>My Orders</b>\n"]
        keyboard = []
        for order in orders:
            emoji = _status_icon(order["status"])
            product = await models.get_product(order["product_id"])
            product_name = product["name"] if product else "Unknown"
            label = (
                f"#{order['id']} | {product_name} | "
                f"{emoji} {order['status']} | "
                f"{CURRENCY_SYMBOL}{order['total_price']}"
            )
            keyboard.append(
                [InlineKeyboardButton(label, callback_data=f"order_{order['id']}")]
            )
        text = "\n".join(lines) + "\nTap an order to view details 👇"
        keyboard.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")])

    markup = InlineKeyboardMarkup(keyboard)

    if edit:
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=markup
        )
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=markup)


async def my_orders_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `myorders` callback — list user's orders (edits message)."""
    await update.callback_query.answer()
    await _show_orders(update, context, edit=True)


async def my_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myorders command — list user's orders (sends new message)."""
    await _show_orders(update, context, edit=False)


async def order_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `order_{id}` callback — show full order details."""
    query = update.callback_query
    await query.answer()

    order_id = int(query.data.split("_", 1)[1])
    order = await models.get_order(order_id)

    if not order:
        await query.edit_message_text(
            "⚠️ Order not found.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="myorders")]]
            ),
        )
        return

    # Verify ownership
    if order["user_id"] != update.effective_user.id:
        await query.edit_message_text(
            "⛔ This order doesn't belong to you.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="myorders")]]
            ),
        )
        return

    product = await models.get_product(order["product_id"])
    product_name = product["name"] if product else "Unknown"
    emoji = _status_icon(order["status"])

    text = (
        f"🧾 <b>Order #{order['id']}</b>\n"
        "\n"
        f"📦 Product: <b>{product_name}</b>\n"
        f"💰 Amount: <b>{CURRENCY_SYMBOL}{order['total_price']}</b>\n"
        f"📋 Status: {emoji} <b>{order['status']}</b>\n"
    )

    # Show delivered key if applicable
    if order["status"].upper() == "DELIVERED" and order.get("delivered_key"):
        text += (
            "\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "🔑 <b>Your Digital Key:</b>\n"
            f"<code>{order['delivered_key']}</code>\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "\n"
            "<i>Tap the key above to copy it.</i>"
        )

    if order["status"].upper() == "REJECTED":
        text += (
            "\n"
            "ℹ️ <i>Your payment was not verified. Contact support if you believe this is an error.</i>"
        )

    keyboard = [[InlineKeyboardButton("🔙 Back to Orders", callback_data="myorders")]]

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )
