from typing import Final

CACHE_EXCLUDED_SHIPPING_TIME = 60 * 3
WEBHOOK_CACHE_DEFAULT_TIMEOUT: int = 5 * 60  # 5 minutes
APP_ID_PREFIX = "app"

MAX_FILTERABLE_CHANNEL_SLUGS_LIMIT = 500

# Set the timeout for the shipping methods cache to 12 hours as it was the lowest
# time labels were valid for when checking documentation for the carriers
# (FedEx, UPS, TNT, DHL).
CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT: Final[int] = 3600 * 12
