from typing import Type

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields.hstore import HStoreField
from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations
from django.db.migrations.operations.base import Operation
from django.db.models import Field

NOOP = migrations.RunPython.noop

h_store_extension: Operation
h_store_field: Type[Field]

if settings.BACKWARD_HSTORE:
    h_store_extension = HStoreExtension()
    h_store_field = HStoreField
else:

    class Noop(Operation):
        def state_forwards(self, app_label, state):
            pass

        def database_forwards(self, app_label, schema_editor, from_state, to_state):
            pass

        def database_backwards(self, app_label, schema_editor, from_state, to_state):
            pass

    h_store_extension = Noop()
    h_store_field = JSONField
