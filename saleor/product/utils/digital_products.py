from datetime import timedelta

from django.contrib.sites.models import Site
from django.utils.timezone import now

from ...account import events as account_events
from ..models import DigitalContentUrl


def get_default_digital_content_settings() -> dict:
    site = Site.objects.get_current()
    settings = site.settings
    return {
        "automatic_fulfillment": (settings.automatic_fulfillment_digital_products),
        "max_downloads": settings.default_digital_max_downloads,
        "url_valid_days": settings.default_digital_url_valid_days,
    }


def digital_content_url_is_valid(content_url: DigitalContentUrl) -> bool:
    """Check if digital url is still valid for customer.

    It takes default settings or digital product's settings
    to check if url is still valid.
    """
    if content_url.content.use_default_settings:
        digital_content_settings = get_default_digital_content_settings()
        url_valid_days = digital_content_settings["url_valid_days"]
        max_downloads = digital_content_settings["max_downloads"]
    else:
        url_valid_days = content_url.content.url_valid_days
        max_downloads = content_url.content.max_downloads

    if url_valid_days is not None:
        valid_days = timedelta(days=url_valid_days)
        valid_until = content_url.created + valid_days
        if now() > valid_until:
            return False

    if max_downloads is not None and max_downloads <= content_url.download_num:
        return False
    return True


def increment_download_count(content_url: DigitalContentUrl):
    content_url.download_num += 1
    content_url.save(update_fields=["download_num"])

    line = content_url.line
    user = line.order.user if line else None

    if user and line:
        account_events.customer_downloaded_a_digital_link_event(
            user=user, order_line=line
        )
