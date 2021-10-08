class MissingType(object):
    def __init__(self, *args, **kwargs):
        pass


try:
    # Postgres fields are only available in Django with psycopg2 installed
    # and we cannot have psycopg2 on PyPy
    from django.contrib.postgres.fields import (
        IntegerRangeField,
        ArrayField,
        HStoreField,
        JSONField as PGJSONField,
        RangeField,
    )
except ImportError:
    IntegerRangeField, ArrayField, HStoreField, PGJSONField, RangeField = (
        MissingType,
    ) * 5

try:
    # JSONField is only available from Django 3.1
    from django.db.models import JSONField
except ImportError:
    JSONField = MissingType
