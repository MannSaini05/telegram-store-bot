"""
Configuration module for the Telegram Digital Store Bot.

Loads environment variables from config.env and validates
that required settings are present. Exports module-level constants.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from config.env in the project root
_env_path = Path(__file__).resolve().parent / "config.env"
load_dotenv(_env_path)

# --- Required Settings ---

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
    print("ERROR: BOT_TOKEN is not set. Copy config.env.example to config.env and fill in your bot token.")
    sys.exit(1)

_admin_chat_id_raw: str = os.getenv("ADMIN_CHAT_ID", "")
if not _admin_chat_id_raw or _admin_chat_id_raw == "your_telegram_chat_id":
    print("ERROR: ADMIN_CHAT_ID is not set. Copy config.env.example to config.env and fill in your Telegram chat ID.")
    sys.exit(1)

try:
    ADMIN_CHAT_ID: int = int(_admin_chat_id_raw)
except ValueError:
    print(f"ERROR: ADMIN_CHAT_ID must be an integer, got '{_admin_chat_id_raw}'.")
    sys.exit(1)

# --- Payment Details ---

UPI_ID: str = os.getenv("UPI_ID", "your@upi")
BANK_NAME: str = os.getenv("BANK_NAME", "Your Bank Name")
BANK_ACCOUNT: str = os.getenv("BANK_ACCOUNT", "XXXXXXXXXXXX")
BANK_IFSC: str = os.getenv("BANK_IFSC", "XXXXXXXXX")

# --- Display Settings ---

CURRENCY_SYMBOL: str = os.getenv("CURRENCY_SYMBOL", "₹")
BOT_NAME: str = os.getenv("BOT_NAME", "Digital Store Bot")
