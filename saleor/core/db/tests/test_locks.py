import pytest
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext

from ..locks import ADVISORY_LOCK_NAMESPACE, AdvisoryLock, acquire_advisory_xact_lock


@pytest.mark.parametrize("lock", list(AdvisoryLock))
def test_emits_lock_query_with_namespace_and_key(lock, db):
    # given
    with CaptureQueriesContext(connection) as ctx:
        # when
        with transaction.atomic():
            acquire_advisory_xact_lock(lock)

    # then
    lock_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if "pg_advisory_xact_lock" in query["sql"]
    ]
    assert len(lock_queries) == 1
    assert f"{ADVISORY_LOCK_NAMESPACE}, {lock.value}" in lock_queries[0]


@pytest.mark.django_db(transaction=True)
def test_raises_outside_atomic_block():
    # when / then
    with pytest.raises(RuntimeError, match="must be called inside an atomic block"):
        acquire_advisory_xact_lock(AdvisoryLock.CATEGORY_TREE)
