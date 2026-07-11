"""Browse catalog handlers — BGMI platform selection, products, and product detail."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CURRENCY_SYMBOL
import models


async def browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the `browse` callback — show BGMI Keys with platform selection."""
    query = update.callback_query
    await query.answer()

    text = (
        "🎯 <b>BGMI Keys</b>\n"
        "\n"
        "Select your platform to view available mods 👇\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📱  <b>Android</b> — BGMI mods for Android\n"
        "🍎  <b>iOS</b> — BGMI mods for iOS\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    keyboard = [
        [
            InlineKeyboardButton("📱 Android", callback_data="platform_android"),
            InlineKeyboardButton("🍎 iOS", callback_data="platform_ios"),
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")],
    ]

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def platform_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `platform_android` / `platform_ios` callbacks — show categories for that platform."""
    query = update.callback_query
    await query.answer()

    platform = query.data.split("_", 1)[1]  # "android" or "ios"

    categories = await models.get_categories()

    # Filter categories by platform keyword
    if platform == "android":
        filtered = [c for c in categories if "android" in c["name"].lower()]
        platform_label = "📱 Android"
    else:
        filtered = [c for c in categories if "ios" in c["name"].lower()]
        platform_label = "🍎 iOS"

    if not filtered:
        text = (
            f"{platform_label} <b>BGMI Mods</b>\n"
            "\n"
            "No products available for this platform yet.\n"
            "Check back soon!"
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="browse")]]
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Show products from all matching categories
    all_products = []
    for cat in filtered:
        products = await models.get_products_by_category(cat["id"])
        all_products.extend(products)

    text = (
        f"{platform_label} <b>BGMI Mods</b>\n"
        "\n"
        "Select a mod to view details 👇"
    )

    keyboard = []
    for prod in all_products:
        stock = await models.get_stock_count(prod["id"])
        stock_indicator = "🟢" if stock > 0 else "🔴"
        label = f"{stock_indicator} {prod['name']} — {CURRENCY_SYMBOL}{prod['price']}"
        keyboard.append(
            [InlineKeyboardButton(label, callback_data=f"prod_{prod['id']}")]
        )

    keyboard.append([InlineKeyboardButton("🔙 Back to Platform", callback_data="browse")])

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `cat_{id}` callbacks — show products in a category."""
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split("_", 1)[1])
    category = await models.get_category(category_id)

    if not category:
        await query.edit_message_text(
            "⚠️ Category not found.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="browse")]]
            ),
        )
        return

    products = await models.get_products_by_category(category_id)

    text = (
        f"{category['emoji']} <b>{category['name']}</b>\n"
        "\n"
    )

    if not products:
        text += "No products in this category yet."
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="browse")]]
        await query.edit_message_text(
            text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    text += "Select a product to view details 👇"

    keyboard = []
    for prod in products:
        stock = await models.get_stock_count(prod["id"])
        stock_indicator = "🟢" if stock > 0 else "🔴"
        label = f"{stock_indicator} {prod['name']} — {CURRENCY_SYMBOL}{prod['price']}"
        keyboard.append(
            [InlineKeyboardButton(label, callback_data=f"prod_{prod['id']}")]
        )

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="browse")])

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle `prod_{id}` callbacks — show detailed product card."""
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_", 1)[1])
    product = await models.get_product(product_id)

    if not product:
        await query.edit_message_text(
            "⚠️ Product not found.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔙 Back", callback_data="browse")]]
            ),
        )
        return

    stock = await models.get_stock_count(product_id)
    stock_text = f"🟢 {stock} keys available" if stock > 0 else "🔴 Out of stock"

    # Determine platform for back button
    category = await models.get_category(product["category_id"])
    if category and "android" in category["name"].lower():
        back_callback = "platform_android"
    elif category and "ios" in category["name"].lower():
        back_callback = "platform_ios"
    else:
        back_callback = "browse"

    text = (
        f"🎯 <b>{product['name']}</b>\n"
        "\n"
        f"{product['description']}\n"
        "\n"
        f"💰 Price: <b>{CURRENCY_SYMBOL}{product['price']}</b>\n"
        f"📊 Stock: {stock_text}\n"
    )

    keyboard = []

    if stock > 0:
        keyboard.append(
            [InlineKeyboardButton("🛒 Buy Now", callback_data=f"buy_{product_id}")]
        )
    else:
        keyboard.append(
            [InlineKeyboardButton("⚠️ Out of Stock", callback_data="noop")]
        )

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=back_callback)])

    await query.edit_message_text(
        text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard)
    )
