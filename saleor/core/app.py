import gc
from typing import Callable, Optional

import opentracing
from django.apps import AppConfig
from django.conf import settings
from django.db.models import Field
from django.utils.module_loading import import_string

from .db.filters import PostgresILike


def set_up_garbage_collector_trace(phase, info):
    if not isinstance(info, dict):
        return
    if info.get("generation", 0) < 1:
        return

    garbage_trance_span = getattr(set_up_garbage_collector_trace, "_span", None)
    global_tracer = opentracing.global_tracer()

    # Check if active span exists to confirm that the we track the active request
    if phase == "start" and global_tracer.active_span:
        set_up_garbage_collector_trace._span = (  # type: ignore[attr-defined]
            global_tracer.start_span("gc")
        )
    elif phase == "stop" and garbage_trance_span:
        garbage_trance_span.set_tag("gc.collected", info["collected"])
        garbage_trance_span.set_tag("gc.uncollectable", info["uncollectable"])
        garbage_trance_span.set_tag("gc.generation", info["generation"])
        garbage_trance_span.finish()


class CoreAppConfig(AppConfig):
    name = "saleor.core"

    def ready(self):
        Field.register_lookup(PostgresILike)

        if settings.SENTRY_DSN:
            settings.SENTRY_INIT(settings.SENTRY_DSN, settings.SENTRY_OPTS)

        if settings.COLLECT_GC_SPANS:
            gc.callbacks.append(set_up_garbage_collector_trace)

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

        validate_method: Optional[Callable[[], None]] = getattr(
            jwt_manager, "validate_configuration", None
        )
        if validate_method is None:
            return
        validate_method()
