"""WSGI config for Saleor project.

This module contains the WSGI application used by Django's development server
and any production WSGI deployments. It should expose a module-level variable
named ``application``. Django's ``runserver`` and ``runfcgi`` commands discover
this application via the ``WSGI_APPLICATION`` setting.

Usually you will have the standard Django WSGI application here, but it also
might make sense to replace the whole Django WSGI application with a custom one
that later delegates to the Django one. For example, you could introduce WSGI
middleware here, or combine a Django application with an application of another
framework.
"""

import os

from django.core.wsgi import get_wsgi_application
from django.utils.functional import SimpleLazyObject

from saleor.wsgi.health_check import health_check


def get_allowed_host_lazy():
    from django.conf import settings

    return settings.ALLOWED_HOSTS[0]


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

application = get_wsgi_application()
application = health_check(application, "/health/")

# Warm-up the django application instead of letting it lazy-load
application(
    {
        "REQUEST_METHOD": "GET",
        "SERVER_NAME": SimpleLazyObject(get_allowed_host_lazy),
        "REMOTE_ADDR": "127.0.0.1",
        "SERVER_PORT": 80,
        "PATH_INFO": "/graphql/",
        "wsgi.input": b"",
        "wsgi.multiprocess": True,
    },
    lambda x, y: None,
)
