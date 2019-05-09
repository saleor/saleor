# Code obtained from django-debug-toolbar sql panel tracking
from __future__ import absolute_import, unicode_literals

import json
from threading import local
from time import time

from django.utils import six
from django.utils.encoding import force_text

from .types import DjangoDebugSQL


class SQLQueryTriggered(Exception):
    """Thrown when template panel triggers a query"""


class ThreadLocalState(local):
    def __init__(self):
        self.enabled = True

    @property
    def Wrapper(self):
        if self.enabled:
            return NormalCursorWrapper
        return ExceptionCursorWrapper

    def recording(self, v):
        self.enabled = v


state = ThreadLocalState()
recording = state.recording  # export function


def wrap_cursor(connection, panel):
    if not hasattr(connection, "_graphene_cursor"):
        connection._graphene_cursor = connection.cursor

        def cursor():
            return state.Wrapper(connection._graphene_cursor(), connection, panel)

        connection.cursor = cursor
        return cursor


def unwrap_cursor(connection):
    if hasattr(connection, "_graphene_cursor"):
        previous_cursor = connection._graphene_cursor
        connection.cursor = previous_cursor
        del connection._graphene_cursor


class ExceptionCursorWrapper(object):
    """
    Wraps a cursor and raises an exception on any operation.
    Used in Templates panel.
    """

    def __init__(self, cursor, db, logger):
        pass

    def __getattr__(self, attr):
        raise SQLQueryTriggered()


class NormalCursorWrapper(object):
    """
    Wraps a cursor and logs queries.
    """

    def __init__(self, cursor, db, logger):
        self.cursor = cursor
        # Instance of a BaseDatabaseWrapper subclass
        self.db = db
        # logger must implement a ``record`` method
        self.logger = logger

    def _quote_expr(self, element):
        if isinstance(element, six.string_types):
            return "'%s'" % force_text(element).replace("'", "''")
        else:
            return repr(element)

    def _quote_params(self, params):
        if not params:
            return params
        if isinstance(params, dict):
            return dict((key, self._quote_expr(value)) for key, value in params.items())
        return list(map(self._quote_expr, params))

    def _decode(self, param):
        try:
            return force_text(param, strings_only=True)
        except UnicodeDecodeError:
            return "(encoded string)"

    def _record(self, method, sql, params):
        start_time = time()
        try:
            return method(sql, params)
        finally:
            stop_time = time()
            duration = stop_time - start_time
            _params = ""
            try:
                _params = json.dumps(list(map(self._decode, params)))
            except Exception:
                pass  # object not JSON serializable

            alias = getattr(self.db, "alias", "default")
            conn = self.db.connection
            vendor = getattr(conn, "vendor", "unknown")

            params = {
                "vendor": vendor,
                "alias": alias,
                "sql": self.db.ops.last_executed_query(
                    self.cursor, sql, self._quote_params(params)
                ),
                "duration": duration,
                "raw_sql": sql,
                "params": _params,
                "start_time": start_time,
                "stop_time": stop_time,
                "is_slow": duration > 10,
                "is_select": sql.lower().strip().startswith("select"),
            }

            if vendor == "postgresql":
                # If an erroneous query was ran on the connection, it might
                # be in a state where checking isolation_level raises an
                # exception.
                try:
                    iso_level = conn.isolation_level
                except conn.InternalError:
                    iso_level = "unknown"
                params.update(
                    {
                        "trans_id": self.logger.get_transaction_id(alias),
                        "trans_status": conn.get_transaction_status(),
                        "iso_level": iso_level,
                        "encoding": conn.encoding,
                    }
                )

            _sql = DjangoDebugSQL(**params)
            # We keep `sql` to maintain backwards compatibility
            self.logger.object.sql.append(_sql)

    def callproc(self, procname, params=()):
        return self._record(self.cursor.callproc, procname, params)

    def execute(self, sql, params=()):
        return self._record(self.cursor.execute, sql, params)

    def executemany(self, sql, param_list):
        return self._record(self.cursor.executemany, sql, param_list)

    def __getattr__(self, attr):
        return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
