from django.apps import AppConfig
from django.conf import settings
from django.db.models import Field
from django.utils.module_loading import import_string

from .db.filters import PostgresILike


class CoreAppConfig(AppConfig):
    name = "saleor.core"

    def ready(self):
        Field.register_lookup(PostgresILike)

        if settings.SENTRY_DSN:
            settings.SENTRY_INIT(settings.SENTRY_DSN, settings.SENTRY_OPTS)
        self.validate_jwt_manager()

    def validate_jwt_manager(self):
        jwt_manager_path = getattr(settings, "JWT_MANAGER_PATH", None)
        if not jwt_manager_path:
            raise ImportError(
                "Missing setting value for JWT Manager path - JWT_MANAGER_PATH"
            )
        try:
            jwt_manager = import_string(jwt_manager_path)
        except ImportError as e:
            raise ImportError(f"Failed to import JWT manager: {e}.")

        validate_method = getattr(jwt_manager, "validate_configuration", NotImplemented)
        if validate_method is NotImplemented:
            return
        validate_method()
