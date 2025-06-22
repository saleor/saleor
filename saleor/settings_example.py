# Telegram Bot Configuration Example
# Add this configuration to your Django settings.py file

import os

# Telegram Bot Token configuration
# Get Bot Token from environment variable
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# If you need to set a default value in development (for testing only)
# TELEGRAM_BOT_TOKEN = "your-telegram-bot-token-here"

# Validate if Bot Token is configured
if not TELEGRAM_BOT_TOKEN:
    print(
        "Warning: TELEGRAM_BOT_TOKEN is not configured, Telegram authentication will be unavailable"
    )
