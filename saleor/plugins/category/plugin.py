import logging
from typing import Optional

from saleor.core.notifications import get_site_context
from saleor.core.notify_events import CategoryNotifyEvent, NotifyEventType
from saleor.plugins.base_plugin import BasePlugin
from saleor.plugins.category.notify_event import send_category_notify

logger = logging.getLogger(__name__)


def get_category_event_map():
    return {
        CategoryNotifyEvent.CATEGORY_EVENT: send_category_notify,
    }


def send_category_notification(manager, channel_slug: Optional[str], staff=False):
    payload = {
        "channel_slug": channel_slug,
        **get_site_context(),
    }

    event = NotifyEventType.CATEGORY_EVENT
    manager.notify(event, payload=payload, channel_slug=channel_slug)


class CategoryPlugin(BasePlugin):
    PLUGIN_ID = "plugin.Category"
    PLUGIN_NAME = "Category Custom"
    PLUGIN_DESCRIPTION = "Description of Category Custom."
    DEFAULT_ACTIVE = True

    def notify(self, event: NotifyEventType, payload: dict, previous_value):
        if not self.active:
            return previous_value
        event_map = get_category_event_map()
        if event not in CategoryNotifyEvent.CHOICES:
            return previous_value
        if event not in event_map:
            logger.warning(f"Missing handler for event {event}")
            return previous_value
        event_map[event]()
