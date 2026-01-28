import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

print(f"DEBUG: ALLOWED_GRAPHQL_ORIGINS = {settings.ALLOWED_GRAPHQL_ORIGINS}")
print(f"DEBUG: ALLOWED_CLIENT_HOSTS = {settings.ALLOWED_CLIENT_HOSTS}")
print(f"DEBUG: CORS_ALLOWED_ORIGINS (if exists) = {getattr(settings, 'CORS_ALLOWED_ORIGINS', 'Not Set')}")
