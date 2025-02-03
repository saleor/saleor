from django.db.backends.base.validation import BaseDatabaseValidation
from django.db.backends.postgresql.client import DatabaseClient
from django.db.backends.postgresql.creation import DatabaseCreation
from django.db.backends.postgresql.features import DatabaseFeatures
from django.db.backends.postgresql.introspection import DatabaseIntrospection
from django.db.backends.postgresql.operations import DatabaseOperations
from django.db.utils import DatabaseErrorWrapper


def __del_connection__(self):
    self.connection = None


def __del_wrapper__(self):
    self.wrapper = None


def patch_db():
    """Patch `__del__` in objects to avoid memory leaks.

    Those changes will remove the circular references between database objects,
    allowing memory to be freed immediately, without the need of a deep garbage collection cycle.
    Issue: https://code.djangoproject.com/ticket/34865
    """
    DatabaseClient.__del__ = __del_connection__  # type: ignore[attr-defined]
    DatabaseCreation.__del__ = __del_connection__  # type: ignore[attr-defined]
    DatabaseFeatures.__del__ = __del_connection__  # type: ignore[attr-defined]
    DatabaseIntrospection.__del__ = __del_connection__  # type: ignore[attr-defined]
    DatabaseOperations.__del__ = __del_connection__  # type: ignore[attr-defined]
    BaseDatabaseValidation.__del__ = __del_connection__  # type: ignore[attr-defined]

    DatabaseErrorWrapper.__del__ = __del_wrapper__  # type: ignore[attr-defined]
