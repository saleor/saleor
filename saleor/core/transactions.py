from contextlib import contextmanager

import opentracing
from django.db import DatabaseError, transaction


@contextmanager
def transaction_with_commit_on_errors():
    """Perform transaction and raise an error in any occurred."""
    error = None
    with transaction.atomic():
        with opentracing.global_tracer().start_active_span(
            "transaction_with_commit_on_errors"
        ) as scope:
            span = scope.span
            span.set_tag(opentracing.tags.COMPONENT, "db")
            try:
                yield
            except DatabaseError:
                raise
            except Exception as e:
                error = e
    if error:
        raise error
