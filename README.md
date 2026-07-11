# 🤖 Telegram Digital Store Bot

A fully-featured Telegram bot for selling digital keys, licenses, and subscriptions — with UPI/bank payment verification, auto-delivery, and admin order management.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🛒 **Product Catalog** | Categories with emoji icons, detailed product cards with stock indicators |
| 💳 **UPI / Bank Payment** | Shows your payment details, customers send screenshot proof |
| 📬 **Auto-Delivery** | Pre-loaded keys are delivered instantly upon approval |
| 🔐 **Manual Delivery** | Admin can send keys manually for out-of-stock items |
| 🔔 **Admin Notifications** | Full order details + payment proof sent to your Telegram |
| ✅ **One-Tap Approve/Reject** | Inline buttons on admin notifications |
| 📊 **Sales Dashboard** | Quick stats on orders, revenue, and pending items |
| 📦 **Order History** | Customers can track all their orders and view delivered keys |

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+** installed
- A **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- Your **Telegram Chat ID** from [@userinfobot](https://t.me/userinfobot)

### 2. Setup

```bash
# Clone or download the project
cd telegram-store-bot

# Install dependencies
pip install -r requirements.txt

# Create your config file
cp config.env.example config.env
```

### 3. Configure

Edit `config.env` with your details:

```env
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
ADMIN_CHAT_ID=123456789
UPI_ID=yourname@upi
BANK_NAME=State Bank of India
BANK_ACCOUNT=1234567890
BANK_IFSC=SBIN0001234
CURRENCY_SYMBOL=₹
BOT_NAME=Beast Keys Store
```

### 4. Run

```bash
python bot.py
```

🎉 Your bot is now live! Open it in Telegram and send `/start`.

---

## 📋 Commands Reference

### Customer Commands
| Command | Description |
|---------|-------------|
| `/start` | Open the main menu |
| `/myorders` | View your order history |

### Admin Commands (only work for ADMIN_CHAT_ID)
| Command | Description |
|---------|-------------|
| `/orders` | List all pending orders with approve/reject buttons |
| `/stats` | View sales dashboard (orders, revenue, pending count) |
| `/sendkey <order_id> <key>` | Manually deliver a key to a customer |
| `/addkeys <product_id>` | Bulk-add keys (send one per line in next message) |
| `/addproduct <cat_id> <price> <name> \| <desc>` | Create a new product |
| `/addcategory <emoji> <name> \| <desc>` | Create a new category |

---

## 🔄 Order Flow

```
Customer browses → Selects product → Sees UPI/bank details
→ Pays externally → Sends screenshot → Order created (PENDING)
→ Admin gets notified → Taps ✅ Approve
→ Key auto-delivered (or admin sends manually)
→ Customer receives key
```

### Order Statuses
| Status | Meaning |
|--------|---------|
| ⏳ PENDING | Awaiting admin payment verification |
| ✅ APPROVED | Payment verified, key pending delivery |
| 📬 DELIVERED | Key sent to customer |
| ❌ REJECTED | Payment verification failed |

---

## 📦 Managing Products & Keys

### Adding Keys to Inventory

```
/addkeys 1
```
Then send your keys, one per line:
```
XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
YYYYY-YYYYY-YYYYY-YYYYY-YYYYY
ZZZZZ-ZZZZZ-ZZZZZ-ZZZZZ-ZZZZZ
```

### Creating a New Product

```
/addproduct 1 799 Windows 11 Pro | Genuine Windows 11 Professional license key
```

### Creating a New Category

```
/addcategory 🎬 Streaming | Streaming service subscription keys
```

---

## 🗄️ Database

The bot uses **SQLite** — all data is stored in a single `store.db` file in the project root. No external database setup needed.

### Tables
- `categories` — Product categories with emoji icons
- `products` — Products with prices, linked to categories
- `digital_keys` — Inventory of digital keys, linked to products
- `orders` — Customer orders with status tracking

### Example Data

On first run, the bot seeds 4 categories and 8 example products:
- 🎮 Game Keys (GTA V, Minecraft)
- 💻 Software (Windows 11, Office 2024)
- 📺 Streaming (Netflix, Spotify)
- 🔐 VPN & Security (NordVPN, Kaspersky)

---

## 🌐 Deployment Options

### Option 1: VPS (Recommended)

Run on any Linux VPS (DigitalOcean, AWS Lightsail, etc.):

```bash
# Use screen or tmux to keep it running
screen -S storebot
python bot.py
# Press Ctrl+A then D to detach
```

Or use **systemd** for auto-restart:

```ini
# /etc/systemd/system/storebot.service
[Unit]
Description=Telegram Store Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/telegram-store-bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### Option 2: Railway / Render

1. Push code to GitHub
2. Connect to [Railway](https://railway.app) or [Render](https://render.com)
3. Set environment variables in dashboard
4. Deploy!

### Option 3: Run Locally

Perfect for testing. Just run `python bot.py` and keep your terminal open.

---

## 📁 Project Structure

```
telegram-store-bot/
├── bot.py                  # Main entry point
├── config.py               # Configuration loader
├── config.env              # Your config (create from .example)
├── config.env.example      # Example configuration
├── database.py             # SQLite database manager
├── models.py               # Data query/mutation functions
├── handlers/
│   ├── __init__.py
│   ├── start.py            # /start & main menu
│   ├── browse.py           # Product browsing
│   ├── cart.py             # Checkout & payment flow
│   ├── payment.py          # Payment proof processing
│   ├── orders.py           # Customer order history
│   └── admin.py            # Admin commands & actions
├── requirements.txt        # Python dependencies
├── store.db                # SQLite database (auto-created)
└── README.md               # This file
```

---

## ⚠️ Security Notes

- Never commit `config.env` to version control
- Keep your BOT_TOKEN secret
- The bot restricts all admin commands to your `ADMIN_CHAT_ID`
- Digital keys are stored in plaintext in SQLite — suitable for most use cases
- For production with sensitive data, consider encrypting the database

---

## 📄 License

This project is for personal/commercial use. Customize it freely for your store!
