"""ASGI config for Saleor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from .cors_handler import cors_handler
from .gzip_compression import gzip_compression
from .health_check import health_check


def preload_app() -> None:
    """Import the app code to make sure that Django application is loaded.

    By default, Django does not import the application until the first request is processed.
    """
    from django.conf import settings
    from django.urls import get_resolver

    get_resolver(settings.ROOT_URLCONF).url_patterns


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

application = get_asgi_application()
application = health_check(application, "/health/")  # type: ignore[arg-type] # Django's ASGI app is less strict than the spec # noqa: E501
application = gzip_compression(application)
application = cors_handler(application)

preload_app()
