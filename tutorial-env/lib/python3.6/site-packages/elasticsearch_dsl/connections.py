from six import string_types

from elasticsearch import Elasticsearch

from .serializer import serializer

class Connections(object):
    """
    Class responsible for holding connections to different clusters. Used as a
    singleton in this module.
    """
    def __init__(self):
        self._kwargs = {}
        self._conns = {}

    def configure(self, **kwargs):
        """
        Configure multiple connections at once, useful for passing in config
        dictionaries obtained from other sources, like Django's settings or a
        configuration management tool.

        Example::

            connections.configure(
                default={'hosts': 'localhost'},
                dev={'hosts': ['esdev1.example.com:9200'], sniff_on_start=True}
            )

        Connections will only be constructed lazily when requested through
        ``get_connection``.
        """
        for k in list(self._conns):
            # try and preserve existing client to keep the persistent connections alive
            if k in self._kwargs and kwargs.get(k, None) == self._kwargs[k]:
                continue
            del self._conns[k]
        self._kwargs = kwargs

    def add_connection(self, alias, conn):
        """
        Add a connection object, it will be passed through as-is.
        """
        self._conns[alias] = conn

    def remove_connection(self, alias):
        """
        Remove connection from the registry. Raises ``KeyError`` if connection
        wasn't found.
        """
        errors = 0
        for d in (self._conns, self._kwargs):
            try:
                del d[alias]
            except KeyError:
                errors += 1

        if errors == 2:
            raise KeyError('There is no connection with alias %r.' % alias)

    def create_connection(self, alias='default', **kwargs):
        """
        Construct an instance of ``elasticsearch.Elasticsearch`` and register
        it under given alias.
        """
        kwargs.setdefault('serializer', serializer)
        conn = self._conns[alias] = Elasticsearch(**kwargs)
        return conn

    def get_connection(self, alias='default'):
        """
        Retrieve a connection, construct it if necessary (only configuration
        was passed to us). If a non-string alias has been passed through we
        assume it's already a client instance and will just return it as-is.

        Raises ``KeyError`` if no client (or its definition) is registered
        under the alias.
        """
        # do not check isinstance(Elasticsearch) so that people can wrap their
        # clients
        if not isinstance(alias, string_types):
            return alias

        # connection already established
        try:
            return self._conns[alias]
        except KeyError:
            pass

        # if not, try to create it
        try:
            return self.create_connection(alias, **self._kwargs[alias])
        except KeyError:
            # no connection and no kwargs to set one up
            raise KeyError('There is no connection with alias %r.' % alias)

connections = Connections()
configure = connections.configure
add_connection = connections.add_connection
remove_connection = connections.remove_connection
create_connection = connections.create_connection
get_connection = connections.get_connection
