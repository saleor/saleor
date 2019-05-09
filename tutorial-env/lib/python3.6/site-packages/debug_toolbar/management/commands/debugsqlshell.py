from __future__ import absolute_import, print_function, unicode_literals

from time import time

import sqlparse
from django.core.management.commands.shell import Command  # noqa
from django.db.backends import utils as db_backends_utils

# 'debugsqlshell' is the same as the 'shell'.


class PrintQueryWrapper(db_backends_utils.CursorDebugWrapper):
    def execute(self, sql, params=()):
        start_time = time()
        try:
            return self.cursor.execute(sql, params)
        finally:
            raw_sql = self.db.ops.last_executed_query(self.cursor, sql, params)
            end_time = time()
            duration = (end_time - start_time) * 1000
            formatted_sql = sqlparse.format(raw_sql, reindent=True)
            print("%s [%.2fms]" % (formatted_sql, duration))


db_backends_utils.CursorDebugWrapper = PrintQueryWrapper
