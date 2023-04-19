from django.conf import settings

from .models import CeleryTask


class PrimaryReplicaRouter:
    def db_for_write(self, model, **hints):
        """Write only to primary. Use separate connection name for CeleryTask mutex."""
        instance = hints.get("instance")
        if isinstance(instance, CeleryTask):
            return settings.DATABASE_CONNECTION_DEFAULT_NAME_ALIAS
        return settings.DATABASE_CONNECTION_DEFAULT_NAME

    def allow_relation(self, obj1, obj2, **hints):
        """All relations are allowed as we don't have pool separation."""
        return True
