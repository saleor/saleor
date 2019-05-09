try:
    import queue
except ImportError:
    import Queue as queue
from .base import Connection


class PoolingConnection(Connection):
    """
    Base connection class for connections that use libraries without thread
    safety and no capacity for connection pooling. To use this just implement a
    ``_make_connection`` method that constructs a new connection and returns
    it.
    """
    def __init__(self, *args, **kwargs):
        self._free_connections = queue.Queue()
        super(PoolingConnection, self).__init__(*args, **kwargs)

    def _get_connection(self):
        try:
            return self._free_connections.get_nowait()
        except queue.Empty:
            return self._make_connection()

    def _release_connection(self, con):
        self._free_connections.put(con)

    def close(self):
        """
        Explicitly close connection
        """
        pass

