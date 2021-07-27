from django.apps import AppConfig
from django.db.models import Field

from .db.filters import PostgresILike


class CoreAppConfig(AppConfig):
    name = "saleor.core"

    def ready(self):
        Field.register_lookup(PostgresILike)
