import os
import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saleor.settings")
django.setup()

print(f"ORIGINS:{settings.ALLOWED_GRAPHQL_ORIGINS}")
