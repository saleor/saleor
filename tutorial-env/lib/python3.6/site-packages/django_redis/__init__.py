# -*- coding: utf-8 -*-

VERSION = (4, 10, 0)
__version__ = '.'.join(map(str, VERSION))


def get_redis_connection(alias='default', write=True):
    """
    Helper used for obtaining a raw redis client.
    """

    from django.core.cache import caches

    cache = caches[alias]

    if not hasattr(cache, "client"):
        raise NotImplementedError("This backend does not support this feature")

    if not hasattr(cache.client, "get_client"):
        raise NotImplementedError("This backend does not support this feature")

    return cache.client.get_client(write)
