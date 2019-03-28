from django.contrib.sites.models import Site
from django.utils.timezone import now
import datetime
from ..models import DigitalContentUrl


def get_default_automatic_fulfillment() -> bool:
    site = Site.objects.get_current()
    return site.settings.automatic_fulfillment_digital_products


def get_default_digital_max_downloads() -> int:
    site = Site.objects.get_current()
    return site.settings.default_digital_max_downloads


def get_default_digital_url_valid_days() -> int:
    site = Site.objects.get_current()
    return site.settings.default_digital_url_valid_days


def digital_content_url_is_valid(content_url: DigitalContentUrl) -> bool:
    """ Check if digital url is still valid for customer. It takes default
    settings or digital product's settings to check if url is still valid"""
    if content_url.content.use_default_settings:
        url_valid_days = get_default_digital_url_valid_days()
        max_downloads = get_default_digital_max_downloads()
    else:
        url_valid_days = content_url.content.url_valid_days
        max_downloads = content_url.content.max_downloads

    if url_valid_days is not None:
        valid_days = datetime.timedelta(days=url_valid_days)
        valid_until = content_url.created + valid_days
        if now() > valid_until:
            return False

    if max_downloads is not None and max_downloads <= content_url.download_num:
        return False
    return True
