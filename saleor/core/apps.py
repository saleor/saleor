import warnings
from collections.abc import Callable

from django.apps import AppConfig
from django.conf import settings
from django.db.models import CharField, TextField
from django.utils.module_loading import import_string
from PIL import Image

from .db.filters import PostgresILike


class CoreAppConfig(AppConfig):
    name = "saleor.core"

    def ready(self) -> None:
        CharField.register_lookup(PostgresILike)
        TextField.register_lookup(PostgresILike)
        if settings.SENTRY_DSN:
            settings.SENTRY_INIT(settings.SENTRY_DSN, settings.SENTRY_OPTS)
        self.validate_jwt_manager()
        self.validate_advisory_lock_namespace_import()
        self.set_pillow_pixel_limit()

    @staticmethod
    def set_pillow_pixel_limit() -> None:
        """Apply `settings.MAX_IMAGE_PIXELS` to Pillow.

        Pillow warns above `Image.MAX_IMAGE_PIXELS` but only raises above *twice* that
        value, so halve our limit to make `MAX_IMAGE_PIXELS` the value actually
        enforced. Assigned once at app startup, so tests cannot override it via the
        `settings` fixture - patch `PIL.Image.MAX_IMAGE_PIXELS` directly instead.

        The halving puts Pillow's warning threshold at half of the enforced limit, so
        every legitimately large image would warn. The warning carries no reference to
        the object being processed, so it is useless for tracking; we log with context
        at the point we catch `DecompressionBombError` instead - hence the filter.
        """
        Image.MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS // 2
        warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)

    def validate_jwt_manager(self) -> None:
        jwt_manager_path = getattr(settings, "JWT_MANAGER_PATH", None)
        if not jwt_manager_path:
            raise ImportError(
                "Missing setting value for JWT Manager path - JWT_MANAGER_PATH"
            )
        try:
            jwt_manager = import_string(jwt_manager_path)
        except ImportError as e:
            raise ImportError(f"Failed to import JWT manager: {e}.") from e

        validate_method: Callable[[], None] | None = getattr(
            jwt_manager, "validate_configuration", None
        )
        if validate_method is None:
            return
        validate_method()

    def validate_advisory_lock_namespace_import(self) -> None:
        namespace_import = settings.ADVISORY_LOCK_NAMESPACE_IMPORT
        if namespace_import is None:
            return
        try:
            import_string(namespace_import)
        except ImportError as e:
            raise ImportError(
                f"Failed to import advisory lock namespace function: {e}."
            ) from e
