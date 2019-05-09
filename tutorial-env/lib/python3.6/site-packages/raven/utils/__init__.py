"""
raven.utils
~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2012 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

import logging
import sys

# Using "NOQA" to preserve export compatibility
from raven.utils.compat import iteritems, string_types  # NOQA
from raven.utils.basic import (  # NOQA
    merge_dicts, varmap, memoize, once, is_namedtuple
)


logger = logging.getLogger('raven.errors')


# We store a cache of module_name->version string to avoid
# continuous imports and lookups of modules
_VERSION_CACHE = {}


def get_version_from_app(module_name, app):
    version = None

    # Try to pull version from pkg_resources first
    # as it is able to detect version tagged with egg_info -b
    try:
        # Importing pkg_resources can be slow, so only import it
        # if we need it.
        import pkg_resources
    except ImportError:
        # pkg_resource is not available on Google App Engine
        pass
    else:
        # pull version from pkg_resources if distro exists
        try:
            return pkg_resources.get_distribution(module_name).version
        except Exception:
            pass

    if hasattr(app, 'get_version'):
        version = app.get_version
    elif hasattr(app, '__version__'):
        version = app.__version__
    elif hasattr(app, 'VERSION'):
        version = app.VERSION
    elif hasattr(app, 'version'):
        version = app.version

    if callable(version):
        version = version()

    if not isinstance(version, (string_types, list, tuple)):
        version = None

    if version is None:
        return None

    if isinstance(version, (list, tuple)):
        version = '.'.join(map(str, version))

    return str(version)


def get_versions(module_list=None):
    if not module_list:
        return {}

    ext_module_list = set()
    for m in module_list:
        parts = m.split('.')
        ext_module_list.update('.'.join(parts[:idx])
                               for idx in range(1, len(parts) + 1))

    versions = {}
    for module_name in ext_module_list:
        if module_name not in _VERSION_CACHE:
            try:
                __import__(module_name)
            except ImportError:
                continue

            try:
                app = sys.modules[module_name]
            except KeyError:
                continue

            try:
                version = get_version_from_app(module_name, app)
            except Exception as e:
                logger.exception(e)
                version = None

            _VERSION_CACHE[module_name] = version
        else:
            version = _VERSION_CACHE[module_name]
        if version is not None:
            versions[module_name] = version
    return versions


def get_auth_header(protocol, timestamp, client, api_key,
                    api_secret=None, **kwargs):
    header = [
        ('sentry_timestamp', timestamp),
        ('sentry_client', client),
        ('sentry_version', protocol),
        ('sentry_key', api_key),
    ]
    if api_secret:
        header.append(('sentry_secret', api_secret))

    return 'Sentry %s' % ', '.join('%s=%s' % (k, v) for k, v in header)
