"""
Configuration module for the Telegram Digital Store Bot.

Loads environment variables from config.env (local dev) or from
OS environment variables (cloud platforms like Render, Railway).
"""

import os
import sys
from pathlib import Path

# Try to load config.env for local development
# On cloud platforms, env vars are set directly in the dashboard
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent / "config.env"
    if _env_path.exists():
        load_dotenv(_env_path)
        print("INFO: Loaded config from config.env")
    else:
        print("INFO: No config.env found, using OS environment variables")
except ImportError:
    print("INFO: python-dotenv not installed, using OS environment variables")

# --- Debug: show which env vars are detected ---
print(f"DEBUG: BOT_TOKEN present = {bool(os.environ.get('BOT_TOKEN'))}")
print(f"DEBUG: ADMIN_CHAT_ID present = {bool(os.environ.get('ADMIN_CHAT_ID'))}")
print(f"DEBUG: DATABASE_URL present = {bool(os.environ.get('DATABASE_URL'))}")
print(f"DEBUG: All env var keys = {[k for k in os.environ.keys() if k in ('BOT_TOKEN','ADMIN_CHAT_ID','DATABASE_URL','UPI_ID','BOT_NAME','CURRENCY_SYMBOL')]}")

# --- Required Settings ---

BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "") or os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
    print("ERROR: BOT_TOKEN is not set. Set it as an environment variable or in config.env.")
    sys.exit(1)

_admin_chat_id_raw: str = os.environ.get("ADMIN_CHAT_ID", "") or os.getenv("ADMIN_CHAT_ID", "")
if not _admin_chat_id_raw or _admin_chat_id_raw == "your_telegram_chat_id":
    print("ERROR: ADMIN_CHAT_ID is not set.")
    sys.exit(1)

try:
    ADMIN_CHAT_ID: int = int(_admin_chat_id_raw)
except ValueError:
    print(f"ERROR: ADMIN_CHAT_ID must be an integer, got '{_admin_chat_id_raw}'.")
    sys.exit(1)

# --- Payment Details ---

UPI_ID: str = os.environ.get("UPI_ID", "your@upi")
BANK_NAME: str = os.environ.get("BANK_NAME", "Your Bank Name")
BANK_ACCOUNT: str = os.environ.get("BANK_ACCOUNT", "XXXXXXXXXXXX")
BANK_IFSC: str = os.environ.get("BANK_IFSC", "XXXXXXXXX")

# --- Display Settings ---

CURRENCY_SYMBOL: str = os.environ.get("CURRENCY_SYMBOL", "₹")
BOT_NAME: str = os.environ.get("BOT_NAME", "JJ Playz Store")

# --- Database ---

DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL is not set.")
    sys.exit(1)
