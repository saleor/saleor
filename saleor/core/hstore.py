from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.hstore import HStoreField
from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations

NOOP = migrations.RunPython.noop

if settings.BACKWARD_HSTORE:
    h_store_extension = HStoreExtension()
    h_store_field = HStoreField
else:
    h_store_extension = NOOP
    h_store_field = JSONField
