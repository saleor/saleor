import logging
from typing import Any

from django.conf import settings
from django.core.management.color import color_style
from django.db.backends.base.base import BaseDatabaseWrapper
from django.db.backends.utils import CursorWrapper

logger = logging.getLogger(__name__)


def db_alias_logger_middleware(get_response):
    def middleware(request):
        from django.db import connections

        for conn in connections.all():
            wrap_connection(conn)

        response = get_response(request)
        return response

    return middleware


def wrap_connection(connection: BaseDatabaseWrapper):
    if not hasattr(connection, "_orig_cursor"):
        connection._orig_cursor = connection.cursor  # type: ignore

        def cursor(*args, **kwargs):
            orig_cursor = connection._orig_cursor(*args, **kwargs)  # type: ignore
            PatchedCursor = _apply_mixin(orig_cursor.__class__, DbAliasLogger)
            return PatchedCursor(orig_cursor.cursor, connection)

        connection.cursor = cursor  # type: ignore[method-assign]


class DbAliasLogger(CursorWrapper):
    def _add_logger(self, method, sql, params):
        alias = self.db.alias

        # Get logger settings.
        log_settings = getattr(settings, "DB_ALIAS_LOGGER", {})
        settings_log_replica = log_settings.get("LOG_REPLICA", False)
        settings_log_writer = log_settings.get("LOG_WRITER", True)

        if alias == settings.DATABASE_CONNECTION_DEFAULT_NAME:
            msg_db_alias = color_style().NOTICE(f"[db:{alias}]")
            msg = (
                "Query executed using default DB alias. Use specific alias instead: "
                f"{settings.DATABASE_CONNECTION_REPLICA_NAME} or "
                f"{settings.DATABASE_CONNECTION_WRITER_NAME}"
            )
            logger.warning("%s: %s; %s", msg_db_alias, sql, msg)
        elif settings_log_writer and alias == settings.DATABASE_CONNECTION_WRITER_NAME:
            msg_db_alias = color_style().WARNING(f"[db:{alias}]")
            logger.info("%s: %s", msg_db_alias, sql)
        elif (
            settings_log_replica and alias == settings.DATABASE_CONNECTION_REPLICA_NAME
        ):
            msg_db_alias = color_style().SUCCESS(f"[db:{alias}]")
            logger.info("%s: %s", msg_db_alias, sql)
        return method(sql, params)

    def execute(self, sql, params=None):
        return self._add_logger(super().execute, sql, params)

    def executemany(self, sql, param_list):
        return self._add_logger(super().executemany, sql, param_list)


def _apply_mixin(base_wrapper: Any, mixin: Any):
    class DbAliasLoggerCursorWrapper(mixin, base_wrapper):
        # Purpose of this class is to combine the mixin and the base_wrapper together.
        pass

    return DbAliasLoggerCursorWrapper
