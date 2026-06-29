from collections.abc import Callable
from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.conf import settings
from django.utils.module_loading import import_string

if TYPE_CHECKING is True:
    from ..graphql.shop.types import Announcement


class SiteAppConfig(AppConfig):
    name = "saleor.site"

    announcements_resolver: Callable[[], list["Announcement"]] | None = None

    @classmethod
    def setup_announcements(cls):
        if settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT is not None:
            cls.announcements_resolver = import_string(
                settings.SHOP_ANNOUNCEMENT_RESOLVER_IMPORT
            )

    def ready(self):
        self.setup_announcements()
