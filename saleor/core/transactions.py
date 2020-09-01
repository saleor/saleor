from contextlib import contextmanager

from django.db import DatabaseError, IntegrityError, transaction


@contextmanager
def transaction_with_commit_on_errors():
    """Perform transaction and raise an error in any occurred."""
    error = None
    with transaction.atomic():
        try:
            yield
        except (DatabaseError, IntegrityError):
            raise
        except Exception as e:
            error = e
    if error:
        raise error
