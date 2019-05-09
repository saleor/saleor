from django.conf import settings
from redis.connection import DefaultParser

from . import util


class ConnectionFactory(object):

    # Store connection pool by cache backend options.
    #
    # _pools is a process-global, as otherwise _pools is cleared every time
    # ConnectionFactory is instiated, as Django creates new cache client
    # (DefaultClient) instance for every request.

    _pools = {}

    def __init__(self, options):
        pool_cls_path = options.get("CONNECTION_POOL_CLASS",
                                    "redis.connection.ConnectionPool")
        self.pool_cls = util.load_class(pool_cls_path)
        self.pool_cls_kwargs = options.get("CONNECTION_POOL_KWARGS", {})

        redis_client_cls_path = options.get("REDIS_CLIENT_CLASS",
                                            "redis.client.StrictRedis")
        self.redis_client_cls = util.load_class(redis_client_cls_path)
        self.redis_client_cls_kwargs = options.get("REDIS_CLIENT_KWARGS", {})

        self.options = options

    def make_connection_params(self, url):
        """
        Given a main connection parameters, build a complete
        dict of connection parameters.
        """

        kwargs = {
            "url": url,
            "parser_class": self.get_parser_cls(),
        }

        password = self.options.get("PASSWORD", None)
        if password:
            kwargs["password"] = password

        socket_timeout = self.options.get("SOCKET_TIMEOUT", None)
        if socket_timeout:
            assert isinstance(socket_timeout, (int, float)), \
                "Socket timeout should be float or integer"
            kwargs["socket_timeout"] = socket_timeout

        socket_connect_timeout = self.options.get("SOCKET_CONNECT_TIMEOUT", None)
        if socket_connect_timeout:
            assert isinstance(socket_connect_timeout, (int, float)), \
                "Socket connect timeout should be float or integer"
            kwargs["socket_connect_timeout"] = socket_connect_timeout

        return kwargs

    def connect(self, url):
        """
        Given a basic connection parameters,
        return a new connection.
        """
        params = self.make_connection_params(url)
        connection = self.get_connection(params)
        return connection

    def get_connection(self, params):
        """
        Given a now preformated params, return a
        new connection.

        The default implementation uses a cached pools
        for create new connection.
        """
        pool = self.get_or_create_connection_pool(params)
        return self.redis_client_cls(connection_pool=pool, **self.redis_client_cls_kwargs)

    def get_parser_cls(self):
        cls = self.options.get("PARSER_CLASS", None)
        if cls is None:
            return DefaultParser
        return util.load_class(cls)

    def get_or_create_connection_pool(self, params):
        """
        Given a connection parameters and return a new
        or cached connection pool for them.

        Reimplement this method if you want distinct
        connection pool instance caching behavior.
        """
        key = params["url"]
        if key not in self._pools:
            self._pools[key] = self.get_connection_pool(params)
        return self._pools[key]

    def get_connection_pool(self, params):
        """
        Given a connection parameters, return a new
        connection pool for them.

        Overwrite this method if you want a custom
        behavior on creating connection pool.
        """
        cp_params = dict(params)
        cp_params.update(self.pool_cls_kwargs)
        pool = self.pool_cls.from_url(**cp_params)

        if pool.connection_kwargs.get("password", None) is None:
            pool.connection_kwargs["password"] = params.get("password", None)
            pool.reset()

        return pool


def get_connection_factory(path=None, options=None):
    if path is None:
        path = getattr(settings, "DJANGO_REDIS_CONNECTION_FACTORY",
                       "django_redis.pool.ConnectionFactory")

    cls = util.load_class(path)
    return cls(options or {})
