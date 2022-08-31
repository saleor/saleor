from django.conf import settings


class PrimaryReplicaRouter:
    def db_for_read(self, model, **hints):
        """Read from replica."""
        return settings.DATABASE_CONNECTION_REPLICA_NAME

    def db_for_write(self, model, **hints):
        """Write only to primary."""
        return settings.DATABASE_CONNECTION_DEFAULT_NAME

    def allow_relation(self, obj1, obj2, **hints):
        """All relations are allowed as we don't have pool separation."""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
