import os

# TODO: restore hardcoded values or move to settings
CACHE_EXCLUDED_SHIPPING_TIME = int(
    os.environ.get("WEBHOOK_CACHE_EXCLUDED_SHIPPING_TIME", 3 * 60)
)
WEBHOOK_CACHE_DEFAULT_TIMEOUT = int(
    os.environ.get("WEBHOOK_CACHE_DEFAULT_TIMEOUT", 5 * 60)
)
APP_ID_PREFIX = "app"
