"""ASGI config for Saleor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

from saleor.asgi.health_check import health_check

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")

application = get_asgi_application()
application = health_check(application, "/health/")
