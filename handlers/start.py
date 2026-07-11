"""Start command and main menu handlers."""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import BOT_NAME


def _main_menu_keyboard() -> InlineKeyboardMarkup:
    """Build the main menu inline keyboard."""
    keyboard = [
        [InlineKeyboardButton("🛒 Browse Products", callback_data="browse")],
        [InlineKeyboardButton("📦 My Orders", callback_data="myorders")],
        [InlineKeyboardButton("💬 Support", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)


def _welcome_text(first_name: str) -> str:
    """Build the welcome message HTML."""
    return (
        f"🎯 <b>Welcome to {BOT_NAME}, {first_name}!</b>\n"
        "\n"
        "Your premium BGMI mod key store by <b>JJ Playz</b>.\n"
        "Get MARS Loader, ZTRAX & King Mod keys\n"
        "delivered instantly after verification! ⚡\n"
        "\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎯  <b>Browse</b> — explore our BGMI mods\n"
        "📦  <b>My Orders</b> — track your purchases\n"
        "💬  <b>Support</b> — get help from our team\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "\n"
        "Pick an option below to get started 👇"
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command — send welcome message with main menu."""
    first_name = update.effective_user.first_name or "there"
    await update.message.reply_text(
        _welcome_text(first_name),
        parse_mode="HTML",
        reply_markup=_main_menu_keyboard(),
    )


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the `menu_main` callback — edit message to show main menu."""
    query = update.callback_query
    await query.answer()

    first_name = update.effective_user.first_name or "there"
    await query.edit_message_text(
        _welcome_text(first_name),
        parse_mode="HTML",
        reply_markup=_main_menu_keyboard(),
    )


async def support_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the `support` callback — show support info."""
    query = update.callback_query
    await query.answer()

    text = (
        "💬 <b>Support</b>\n"
        "\n"
        "Need help with an order or have a question?\n"
        "Contact our admin directly for assistance.\n"
        "\n"
        "We typically respond within a few hours. 🙏"
    )
    keyboard = [[InlineKeyboardButton("🔙 Back to Menu", callback_data="menu_main")]]
    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
