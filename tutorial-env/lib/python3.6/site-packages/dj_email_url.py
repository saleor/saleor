# -*- coding: utf-8 -*-

import os
import warnings

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


# Register email schemes in URLs.
urlparse.uses_netloc.append('smtp')
urlparse.uses_netloc.append('console')
urlparse.uses_netloc.append('file')
urlparse.uses_netloc.append('memory')
urlparse.uses_netloc.append('dummy')


DEFAULT_ENV = 'EMAIL_URL'


SCHEMES = {
    'smtp': 'django.core.mail.backends.smtp.EmailBackend',
    'submission': 'django.core.mail.backends.smtp.EmailBackend',
    'submit': 'django.core.mail.backends.smtp.EmailBackend',
    'smtps': 'django.core.mail.backends.smtp.EmailBackend',  # pend deprecation
    'console': 'django.core.mail.backends.console.EmailBackend',
    'file': 'django.core.mail.backends.filebased.EmailBackend',
    'memory': 'django.core.mail.backends.locmem.EmailBackend',
    'dummy': 'django.core.mail.backends.dummy.EmailBackend'
}


TRUTHY = (
    '1',
    'y', 'Y', 'yes', 'Yes', 'YES',
    't', 'T', 'true', 'True', 'TRUE',
    'on', 'On', 'ON',
)


def unquote(value):
    return urlparse.unquote(value) if value else value


def config(env=DEFAULT_ENV, default=None):
    """Returns a dictionary with EMAIL_* settings from EMAIL_URL."""

    conf = {}

    s = os.environ.get(env, default)

    if s:
        conf = parse(s)

    return conf


def parse(url):
    """Parses an email URL."""

    conf = {}

    url = urlparse.urlparse(url)
    qs = urlparse.parse_qs(url.query)

    # Remove query strings
    path = url.path[1:]
    path = path.split('?', 2)[0]

    # Update with environment configuration
    conf.update({
        'EMAIL_FILE_PATH': path,
        'EMAIL_HOST_USER': unquote(url.username),
        'EMAIL_HOST_PASSWORD': unquote(url.password),
        'EMAIL_HOST': url.hostname,
        'EMAIL_PORT': url.port,
        'EMAIL_USE_SSL': False,
        'EMAIL_USE_TLS': False,
    })

    if url.scheme in SCHEMES:
        conf['EMAIL_BACKEND'] = SCHEMES[url.scheme]

    # Set defaults for `smtp`
    if url.scheme == 'smtp':
        if not conf['EMAIL_HOST']:
            conf['EMAIL_HOST'] = 'localhost'
        if not conf['EMAIL_PORT']:
            conf['EMAIL_PORT'] = 25

    # Set defaults for `smtps`
    if url.scheme == 'smtps':
        warnings.warn(
            "`smpts` scheme will be deprecated in a future version,"
            " use `submission` instead",
            UserWarning,
        )
        conf['EMAIL_USE_TLS'] = True

    # Set defaults for `submission`/`submit`
    if url.scheme in ('submission', 'submit'):
        conf['EMAIL_USE_TLS'] = True
        if not conf['EMAIL_PORT']:
            conf['EMAIL_PORT'] = 587

    # Query args overwrite defaults
    if 'ssl' in qs and qs['ssl']:
        if qs['ssl'][0] in TRUTHY:
            conf['EMAIL_USE_SSL'] = True
            conf['EMAIL_USE_TLS'] = False
    elif 'tls' in qs and qs['tls']:
        if qs['tls'][0] in TRUTHY:
            conf['EMAIL_USE_SSL'] = False
            conf['EMAIL_USE_TLS'] = True

    # From addresses
    if '_server_email' in qs:
        conf['SERVER_EMAIL'] = qs['_server_email'][0]
    if '_default_from_email' in qs:
        conf['DEFAULT_FROM_EMAIL'] = qs['_default_from_email'][0]

    return conf
