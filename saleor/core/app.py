from django.apps import AppConfig
from django.conf import settings
from django.db.models import Field

from .db.filters import PostgresILike


class CoreAppConfig(AppConfig):
    name = "saleor.core"

    def ready(self):
        Field.register_lookup(PostgresILike)

        if settings.SENTRY_DSN:
            settings.SENTRY_INIT(settings.SENTRY_DSN, settings.SENTRY_OPTS)
