# -*- coding: utf-8 -*-
import os
import re

try:
    import urllib.parse as urlparse
except ImportError:  # python 2
    import urlparse


# Register cache schemes in URLs.
urlparse.uses_netloc.append('db')
urlparse.uses_netloc.append('dummy')
urlparse.uses_netloc.append('file')
urlparse.uses_netloc.append('locmem')
urlparse.uses_netloc.append('uwsgicache')
urlparse.uses_netloc.append('memcached')
urlparse.uses_netloc.append('elasticache')
urlparse.uses_netloc.append('djangopylibmc')
urlparse.uses_netloc.append('pymemcached')
urlparse.uses_netloc.append('redis')
urlparse.uses_netloc.append('hiredis')

DEFAULT_ENV = 'CACHE_URL'

BACKENDS = {
    'db': 'django.core.cache.backends.db.DatabaseCache',
    'dummy': 'django.core.cache.backends.dummy.DummyCache',
    'elasticache': 'django_elasticache.memcached.ElastiCache',
    'file': 'django.core.cache.backends.filebased.FileBasedCache',
    'locmem': 'django.core.cache.backends.locmem.LocMemCache',
    'uwsgicache': 'uwsgicache.UWSGICache',
    'memcached': 'django.core.cache.backends.memcached.PyLibMCCache',
    'djangopylibmc': 'django_pylibmc.memcached.PyLibMCCache',
    'pymemcached': 'django.core.cache.backends.memcached.MemcachedCache',
    'redis': 'django_redis.cache.RedisCache',
    'hiredis': 'django_redis.cache.RedisCache',
}


def config(env=DEFAULT_ENV, default='locmem://'):
    """Returns configured CACHES dictionary from CACHE_URL"""
    config = {}

    s = os.environ.get(env, default)

    if s:
        config = parse(s)

    return config


def parse(url):
    """Parses a cache URL."""
    config = {}

    url = urlparse.urlparse(url)
    # Handle python 2.6 broken url parsing
    path, query = url.path, url.query
    if '?' in path and query == '':
        path, query = path.split('?', 1)

    cache_args = dict([(key.upper(), ';'.join(val)) for key, val in
                       urlparse.parse_qs(query).items()])

    # Update with environment configuration.
    backend = BACKENDS.get(url.scheme)
    if not backend:
        raise Exception('Unknown backend: "{0}"'.format(url.scheme))

    config['BACKEND'] = BACKENDS[url.scheme]

    redis_options = {}
    if url.scheme == 'hiredis':
        redis_options['PARSER_CLASS'] = 'redis.connection.HiredisParser'

    # File based
    if not url.netloc:
        if url.scheme in ('memcached', 'pymemcached', 'djangopylibmc'):
            config['LOCATION'] = 'unix:' + path

        elif url.scheme in ('redis', 'hiredis'):
            match = re.match(r'.+?(?P<db>\d+)', path)
            if match:
                db = match.group('db')
                path = path[:path.rfind('/')]
            else:
                db = '0'
            config['LOCATION'] = 'unix:%s:%s' % (path, db)
        else:
            config['LOCATION'] = path
    # URL based
    else:
        # Handle multiple hosts
        config['LOCATION'] = ';'.join(url.netloc.split(','))

        if url.scheme in ('redis', 'hiredis'):
            if url.password:
                redis_options['PASSWORD'] = url.password
            # Specifying the database is optional, use db 0 if not specified.
            db = path[1:] or '0'
            port = url.port if url.port else 6379
            config['LOCATION'] = "redis://%s:%s/%s" % (url.hostname, port, db)

    if redis_options:
        config.setdefault('OPTIONS', {}).update(redis_options)

    if url.scheme == 'uwsgicache':
        config['LOCATION'] = config.get('LOCATION', 'default') or 'default'

    # Pop special options from cache_args
    # https://docs.djangoproject.com/en/1.10/topics/cache/#cache-arguments
    options = {}
    for key in ['MAX_ENTRIES', 'CULL_FREQUENCY']:
        val = cache_args.pop(key, None)
        if val is not None:
            options[key] = int(val)
    if options:
        config.setdefault('OPTIONS', {}).update(options)

    config.update(cache_args)

    return config
