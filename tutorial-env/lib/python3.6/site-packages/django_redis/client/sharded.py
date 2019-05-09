# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import re
from collections import OrderedDict

from django.conf import settings
from django.utils.encoding import smart_text
from django.utils.six import text_type
from redis.exceptions import ConnectionError

from ..exceptions import ConnectionInterrupted
from ..hash_ring import HashRing
from ..util import CacheKey
from .default import DEFAULT_TIMEOUT, DefaultClient


class ShardClient(DefaultClient):
    _findhash = re.compile(r'.*\{(.*)\}.*', re.I)

    def __init__(self, *args, **kwargs):
        super(ShardClient, self).__init__(*args, **kwargs)

        if not isinstance(self._server, (list, tuple)):
            self._server = [self._server]

        self._ring = HashRing(self._server)
        self._serverdict = self.connect()

    def get_client(self, write=True):
        raise NotImplementedError

    def connect(self):
        connection_dict = {}
        for name in self._server:
            connection_dict[name] = self.connection_factory.connect(name)
        return connection_dict

    def get_server_name(self, _key):
        key = text_type(_key)
        g = self._findhash.match(key)
        if g is not None and len(g.groups()) > 0:
            key = g.groups()[0]
        name = self._ring.get_node(key)
        return name

    def get_server(self, key):
        name = self.get_server_name(key)
        return self._serverdict[name]

    def add(self, key, value, timeout=DEFAULT_TIMEOUT, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self)\
            .add(key=key, value=value, version=version, client=client, timeout=timeout)

    def get(self, key, default=None, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self)\
            .get(key=key, default=default, version=version, client=client)

    def get_many(self, keys, version=None):
        if not keys:
            return {}

        recovered_data = OrderedDict()

        new_keys = [self.make_key(key, version=version) for key in keys]
        map_keys = dict(zip(new_keys, keys))

        for key in new_keys:
            client = self.get_server(key)
            value = self.get(key=key, version=version, client=client)

            if value is None:
                continue

            recovered_data[map_keys[key]] = value
        return recovered_data

    def set(self, key, value, timeout=DEFAULT_TIMEOUT, version=None, client=None, nx=False):
        """
        Persist a value to the cache, and set an optional expiration time.
        """
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self).set(key=key, value=value,
                                            timeout=timeout, version=version,
                                            client=client, nx=nx)

    def set_many(self, data, timeout=DEFAULT_TIMEOUT, version=None):
        """
        Set a bunch of values in the cache at once from a dict of key/value
        pairs. This is much more efficient than calling set() multiple times.

        If timeout is given, that timeout will be used for the key; otherwise
        the default cache timeout will be used.
        """
        for key, value in data.items():
            self.set(key, value, timeout, version=version)

    def has_key(self, key, version=None, client=None):
        """
        Test if key exists.
        """

        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        key = self.make_key(key, version=version)
        try:
            return client.exists(key) == 1
        except ConnectionError:
            raise ConnectionInterrupted(connection=client)

    def delete(self, key, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self).delete(key=key, version=version, client=client)

    def ttl(self, key, version=None, client=None):
        """
        Executes TTL redis command and return the "time-to-live" of specified key.
        If key is a non volatile key, it returns None.
        """

        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self).ttl(key=key, version=version, client=client)

    def persist(self, key, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self).persist(key=key, version=version, client=client)

    def expire(self, key, timeout, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self).expire(key=key, timeout=timeout,
                                               version=version, client=client)

    def lock(self, key, version=None, timeout=None, sleep=0.1,
             blocking_timeout=None, client=None):

        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        key = self.make_key(key, version=version)
        return super(ShardClient, self).lock(key, timeout=timeout, sleep=sleep, client=client,
                                             blocking_timeout=blocking_timeout)

    def delete_many(self, keys, version=None):
        """
        Remove multiple keys at once.
        """
        res = 0
        for key in [self.make_key(k, version=version) for k in keys]:
            client = self.get_server(key)
            res += self.delete(key, client=client)
        return res

    def incr_version(self, key, delta=1, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        if version is None:
            version = self._backend.version

        old_key = self.make_key(key, version)
        value = self.get(old_key, version=version, client=client)

        try:
            ttl = client.ttl(old_key)
        except ConnectionError:
            raise ConnectionInterrupted(connection=client)

        if value is None:
            raise ValueError("Key '%s' not found" % key)

        if isinstance(key, CacheKey):
            new_key = self.make_key(key.original_key(), version=version + delta)
        else:
            new_key = self.make_key(key, version=version + delta)

        self.set(new_key, value, timeout=ttl, client=self.get_server(new_key))
        self.delete(old_key, client=client)
        return version + delta

    def incr(self, key, delta=1, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self)\
            .incr(key=key, delta=delta, version=version, client=client)

    def decr(self, key, delta=1, version=None, client=None):
        if client is None:
            key = self.make_key(key, version=version)
            client = self.get_server(key)

        return super(ShardClient, self)\
            .decr(key=key, delta=delta, version=version, client=client)

    def iter_keys(self, key, version=None):
        raise NotImplementedError("iter_keys not supported on sharded client")

    def keys(self, search, version=None):
        pattern = self.make_key(search, version=version)
        keys = []
        try:
            for server, connection in self._serverdict.items():
                keys.extend(connection.keys(pattern))
        except ConnectionError:
            # FIXME: technically all clients should be passed as `connection`.
            client = self.get_server(pattern)
            raise ConnectionInterrupted(connection=client)

        decoded_keys = (smart_text(k) for k in keys)
        return [self.reverse_key(k) for k in decoded_keys]

    def delete_pattern(self, pattern, version=None, client=None, itersize=None, prefix=None):
        """
        Remove all keys matching pattern.
        """
        pattern = self.make_pattern(pattern, version=version, prefix=prefix)
        kwargs = {'match': pattern}
        if itersize:
            kwargs['count'] = itersize

        keys = []
        for server, connection in self._serverdict.items():
            keys.extend(key for key in connection.scan_iter(**kwargs))

        res = 0
        if keys:
            for server, connection in self._serverdict.items():
                res += connection.delete(*keys)
        return res

    def close(self, **kwargs):
        if getattr(settings, "DJANGO_REDIS_CLOSE_CONNECTION", False):
            for client in self._serverdict.values():
                for c in client.connection_pool._available_connections:
                    c.disconnect()
