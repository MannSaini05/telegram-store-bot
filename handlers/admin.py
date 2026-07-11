"""Admin handlers — order management, key management, product/category creation, stats."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_CHAT_ID, CURRENCY_SYMBOL
import models


# ── Helpers ──────────────────────────────────────────────────────────────────

def _is_admin(update: Update) -> bool:
    """Check if the effective user is the admin."""
    return update.effective_user.id == ADMIN_CHAT_ID


async def _deny(update: Update) -> None:
    """Send an unauthorized message. Works for both messages and callbacks."""
    text = "⛔ <b>Unauthorized</b>\n\nThis action is restricted to the admin."
    if update.callback_query:
        await update.callback_query.answer("⛔ Unauthorized", show_alert=True)
    elif update.message:
        await update.message.reply_text(text, parse_mode="HTML")


_STATUS_EMOJI = {
    "PENDING": "⏳",
    "APPROVED": "✅",
    "DELIVERED": "📬",
    "REJECTED": "❌",
    "CANCELLED": "🚫",
}


# ── Approve / Reject callbacks ──────────────────────────────────────────────

async def approve_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `approve_{id}` callback — approve an order and deliver key if available."""
    query = update.callback_query
    await query.answer()

    if not _is_admin(update):
        await _deny(update)
        return

    order_id = int(query.data.split("_", 1)[1])
    order = await models.get_order(order_id)

    if not order:
        await query.edit_message_text("⚠️ Order not found.", parse_mode="HTML")
        return

    if order["status"].upper() != "PENDING":
        await query.edit_message_text(
            f"ℹ️ Order #{order_id} is already <b>{order['status']}</b>.",
            parse_mode="HTML",
        )
        return

    product = await models.get_product(order["product_id"])
    product_name = product["name"] if product else "Unknown"

    # Try to auto-deliver a key
    key_record = await models.get_available_key(order["product_id"])

    if key_record:
        # Full delivery: mark key sold, attach to order, set DELIVERED
        await models.mark_key_sold(key_record["id"], order_id)
        await models.set_order_delivered_key(order_id, key_record["value"])
        await models.update_order_status(order_id, "DELIVERED")

        # Notify customer with key
        customer_text = (
            f"📬 <b>Order #{order_id} — Delivered!</b>\n"
            "\n"
            f"📦 Product: <b>{product_name}</b>\n"
            "\n"
            "🔑 <b>Your Digital Key:</b>\n"
            f"<code>{key_record['key_value']}</code>\n"
            "\n"
            "<i>Tap the key to copy it. Enjoy! 🎉</i>"
        )
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=customer_text,
            parse_mode="HTML",
        )

        # Update admin message
        await query.edit_message_text(
            f"✅ Order <b>#{order_id}</b> — <b>DELIVERED</b>\n"
            f"🔑 Key: <code>{key_record['key_value']}</code>",
            parse_mode="HTML",
        )
    else:
        # No key in stock — approve but don't deliver yet
        await models.update_order_status(order_id, "APPROVED")

        # Notify customer
        customer_text = (
            f"✅ <b>Order #{order_id} — Approved!</b>\n"
            "\n"
            f"📦 Product: <b>{product_name}</b>\n"
            "\n"
            "Your payment has been verified! 🎉\n"
            "Your digital key will be sent to you shortly."
        )
        await context.bot.send_message(
            chat_id=order["user_id"],
            text=customer_text,
            parse_mode="HTML",
        )

        # Update admin message
        await query.edit_message_text(
            f"✅ Order <b>#{order_id}</b> — <b>APPROVED</b>\n"
            "⚠️ No keys in stock. Use /sendkey to deliver manually.",
            parse_mode="HTML",
        )


async def reject_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `reject_{id}` callback — reject an order."""
    query = update.callback_query
    await query.answer()

    if not _is_admin(update):
        await _deny(update)
        return

    order_id = int(query.data.split("_", 1)[1])
    order = await models.get_order(order_id)

    if not order:
        await query.edit_message_text("⚠️ Order not found.", parse_mode="HTML")
        return

    if order["status"].upper() != "PENDING":
        await query.edit_message_text(
            f"ℹ️ Order #{order_id} is already <b>{order['status']}</b>.",
            parse_mode="HTML",
        )
        return

    await models.update_order_status(order_id, "REJECTED")

    product = await models.get_product(order["product_id"])
    product_name = product["name"] if product else "Unknown"

    # Notify customer
    customer_text = (
        f"❌ <b>Order #{order_id} — Rejected</b>\n"
        "\n"
        f"📦 Product: <b>{product_name}</b>\n"
        "\n"
        "Your payment could not be verified.\n"
        "If you believe this is a mistake, please contact support."
    )
    await context.bot.send_message(
        chat_id=order["user_id"],
        text=customer_text,
        parse_mode="HTML",
    )

    # Update admin message
    await query.edit_message_text(
        f"❌ Order <b>#{order_id}</b> — <b>REJECTED</b>",
        parse_mode="HTML",
    )


# ── /sendkey command ────────────────────────────────────────────────────────

async def sendkey_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /sendkey <order_id> <key_value> — manually deliver a key to a customer."""
    if not _is_admin(update):
        await _deny(update)
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "ℹ️ <b>Usage:</b> <code>/sendkey &lt;order_id&gt; &lt;key_value&gt;</code>",
            parse_mode="HTML",
        )
        return

    try:
        order_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid order ID.", parse_mode="HTML")
        return

    key_value = " ".join(context.args[1:])

    order = await models.get_order(order_id)
    if not order:
        await update.message.reply_text(
            f"⚠️ Order #{order_id} not found.", parse_mode="HTML"
        )
        return

    if order["status"].upper() not in ("APPROVED", "PENDING"):
        await update.message.reply_text(
            f"⚠️ Order #{order_id} is <b>{order['status']}</b>. "
            "Can only send keys for PENDING or APPROVED orders.",
            parse_mode="HTML",
        )
        return

    product = await models.get_product(order["product_id"])
    product_name = product["name"] if product else "Unknown"

    await models.set_order_delivered_key(order_id, key_value)
    await models.update_order_status(order_id, "DELIVERED")

    # Notify customer
    customer_text = (
        f"📬 <b>Order #{order_id} — Delivered!</b>\n"
        "\n"
        f"📦 Product: <b>{product_name}</b>\n"
        "\n"
        "🔑 <b>Your Digital Key:</b>\n"
        f"<code>{key_value}</code>\n"
        "\n"
        "<i>Tap the key to copy it. Enjoy! 🎉</i>"
    )
    await context.bot.send_message(
        chat_id=order["user_id"],
        text=customer_text,
        parse_mode="HTML",
    )

    # Confirm to admin
    await update.message.reply_text(
        f"✅ Key delivered for Order <b>#{order_id}</b>.\n"
        f"🔑 <code>{key_value}</code>",
        parse_mode="HTML",
    )


# ── /addkeys command (two-step) ─────────────────────────────────────────────

async def addkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addkeys <product_id> — start interactive key-adding flow."""
    if not _is_admin(update):
        await _deny(update)
        return

    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "ℹ️ <b>Usage:</b> <code>/addkeys &lt;product_id&gt;</code>\n"
            "Then send the keys, one per line.",
            parse_mode="HTML",
        )
        return

    try:
        product_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("⚠️ Invalid product ID.", parse_mode="HTML")
        return

    product = await models.get_product(product_id)
    if not product:
        await update.message.reply_text(
            f"⚠️ Product #{product_id} not found.", parse_mode="HTML"
        )
        return

    context.user_data["adding_keys_product"] = product_id

    await update.message.reply_text(
        f"📝 <b>Add Keys for:</b> {product['name']}\n"
        "\n"
        "Send the digital keys now, <b>one per line</b>.\n"
        "I'll add them all to the inventory.",
        parse_mode="HTML",
    )


async def addkeys_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages when admin is in the key-adding flow."""
    product_id = context.user_data.get("adding_keys_product")
    if not product_id:
        return  # Not in key-adding mode

    if not _is_admin(update):
        return

    raw_text = update.message.text or ""
    keys_list = [line.strip() for line in raw_text.splitlines() if line.strip()]

    if not keys_list:
        await update.message.reply_text(
            "⚠️ No valid keys found. Send keys one per line.",
            parse_mode="HTML",
        )
        return

    count = await models.add_digital_keys(product_id, keys_list)

    # Clear flag
    context.user_data.pop("adding_keys_product", None)

    product = await models.get_product(product_id)
    product_name = product["name"] if product else f"#{product_id}"

    await update.message.reply_text(
        f"✅ <b>{count}</b> key(s) added to <b>{product_name}</b>.\n"
        f"📊 New stock: <b>{await models.get_stock_count(product_id)}</b>",
        parse_mode="HTML",
    )


# ── /addproduct command ─────────────────────────────────────────────────────

async def addproduct_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addproduct <category_id> <price> <name> | <description>."""
    if not _is_admin(update):
        await _deny(update)
        return

    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "ℹ️ <b>Usage:</b>\n"
            "<code>/addproduct &lt;category_id&gt; &lt;price&gt; &lt;name&gt; | &lt;description&gt;</code>\n"
            "\n"
            "<b>Example:</b>\n"
            "<code>/addproduct 1 499 Netflix Premium | 1 Month Netflix Premium subscription key</code>",
            parse_mode="HTML",
        )
        return

    try:
        category_id = int(context.args[0])
        price = float(context.args[1])
    except ValueError:
        await update.message.reply_text(
            "⚠️ Invalid category_id or price. Both must be numbers.",
            parse_mode="HTML",
        )
        return

    # Everything after the first two args is "name | description"
    rest = " ".join(context.args[2:])
    if "|" in rest:
        name, description = rest.split("|", 1)
        name = name.strip()
        description = description.strip()
    else:
        name = rest.strip()
        description = ""

    if not name:
        await update.message.reply_text(
            "⚠️ Product name cannot be empty.", parse_mode="HTML"
        )
        return

    category = await models.get_category(category_id)
    if not category:
        await update.message.reply_text(
            f"⚠️ Category #{category_id} not found.", parse_mode="HTML"
        )
        return

    product_id = await models.add_product(category_id, name, description, price)

    await update.message.reply_text(
        f"✅ <b>Product Created!</b>\n"
        "\n"
        f"🆔 ID: <b>#{product_id}</b>\n"
        f"📦 Name: <b>{name}</b>\n"
        f"💰 Price: <b>{CURRENCY_SYMBOL}{price}</b>\n"
        f"📂 Category: <b>{category['name']}</b>\n"
        f"📝 Description: {description or '<i>none</i>'}\n"
        "\n"
        f"Use <code>/addkeys {product_id}</code> to add digital keys.",
        parse_mode="HTML",
    )


# ── /addcategory command ────────────────────────────────────────────────────

async def addcategory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /addcategory <emoji> <name> | <description>."""
    if not _is_admin(update):
        await _deny(update)
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "ℹ️ <b>Usage:</b>\n"
            "<code>/addcategory &lt;emoji&gt; &lt;name&gt; | &lt;description&gt;</code>\n"
            "\n"
            "<b>Example:</b>\n"
            "<code>/addcategory 🎬 Streaming | Streaming service subscription keys</code>",
            parse_mode="HTML",
        )
        return

    emoji = context.args[0]
    rest = " ".join(context.args[1:])
    if "|" in rest:
        name, description = rest.split("|", 1)
        name = name.strip()
        description = description.strip()
    else:
        name = rest.strip()
        description = ""

    if not name:
        await update.message.reply_text(
            "⚠️ Category name cannot be empty.", parse_mode="HTML"
        )
        return

    category_id = await models.add_category(name, description, emoji)

    await update.message.reply_text(
        f"✅ <b>Category Created!</b>\n"
        "\n"
        f"🆔 ID: <b>#{category_id}</b>\n"
        f"{emoji} Name: <b>{name}</b>\n"
        f"📝 Description: {description or '<i>none</i>'}",
        parse_mode="HTML",
    )


# ── /stats command ──────────────────────────────────────────────────────────

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats — show store dashboard with order statistics."""
    if not _is_admin(update):
        await _deny(update)
        return

    stats = await models.get_order_stats()

    text = (
        "📊 <b>Store Dashboard</b>\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"📦 Total Orders: <b>{stats['total_orders']}</b>\n"
        f"⏳ Pending: <b>{stats['pending_count']}</b>\n"
        f"✅ Approved: <b>{stats['approved_count']}</b>\n"
        f"📬 Delivered: <b>{stats['delivered_count']}</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"💰 Revenue: <b>{CURRENCY_SYMBOL}{stats['total_revenue']}</b>\n"
    )

    await update.message.reply_text(text, parse_mode="HTML")


# ── /orders command (admin — pending orders) ────────────────────────────────

async def pending_orders_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /orders — list all pending orders with approve/reject buttons."""
    if not _is_admin(update):
        await _deny(update)
        return

    orders = await models.get_pending_orders()

    if not orders:
        await update.message.reply_text(
            "✅ No pending orders. All caught up! 🎉",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"⏳ <b>Pending Orders ({len(orders)})</b>\n",
        parse_mode="HTML",
    )

    for order in orders:
        product = await models.get_product(order["product_id"])
        product_name = product["name"] if product else "Unknown"

        text = (
            f"🧾 <b>Order #{order['id']}</b>\n"
            f"👤 @{order.get('username', 'N/A')} ({order.get('first_name', 'Customer')})\n"
            f"📦 {product_name}\n"
            f"💰 {CURRENCY_SYMBOL}{order['total_price']}"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{order['id']}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{order['id']}"),
            ]
        ]

        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
