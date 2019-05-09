import maxminddb

from threading import Lock
from datetime import datetime

from _maxminddb_geolite2 import geolite2_database


class DatabaseInfo(object):
    """Provides information about the GeoIP database."""

    def __init__(self, filename=None, date=None,
                 internal_name=None):
        #: If available the filename which backs the database.
        self.filename = filename
        #: Optionally the build date of the database as datetime object.
        self.date = date
        #: Optionally the internal name of the database.
        self.internal_name = internal_name

    def __repr__(self):
        return '<%s filename=%r date=%r internal_name=%r>' % (
            self.__class__.__name__,
            self.filename,
            self.date,
            self.internal_name,
        )


class MaxMindDb(object):
    """Provides access to the packaged GeoLite2 database."""

    def __init__(self, filename):
        self.filename = filename
        self._lock = Lock()
        self._reader = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.close()

    def close(self):
        with self._lock:
            if self._reader is not None:
                self._reader.close()
                self._reader = None

    def get_info(self):
        return DatabaseInfo(
            filename=self.filename,
            date=datetime.utcfromtimestamp(self.reader().metadata().build_epoch),
            internal_name=self.reader().metadata().database_type,
        )

    def _open_packaged_database(self):
        return maxminddb.open_database(self.filename)

    def reader(self):
        if self._reader is not None:
            return self._reader
        with self._lock:
            if self._reader is not None:
                return self._reader
            rv = self._open_packaged_database()
            self._reader = rv
            return rv


#: Provides access to the geolite2 cities database.
geolite2 = MaxMindDb(filename=geolite2_database())
