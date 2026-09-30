"""Install due-work-harness's Django host for the contracts in this directory.

The harness reads its host while it generates a contract's cases, so the host is
installed here, before the test modules beside this file are collected. Nothing
outside this directory reads it, and Saleor's own fixtures, which the contracts
use, come from the root conftest as for every other test.
"""

from due_work_harness import configure
from due_work_harness.integrations.celery import celery_publication_breaker
from due_work_harness.integrations.django import django_host

# The system under test is Saleor, reached through Django: every binding must
# call into one of them. Saleor publishes through Celery, so each publication can
# be refused as a broker that is down would refuse it. The lifecycle-state proofs
# are off: they need a sweep to declare the state fields its selection filters on,
# and automatic completion selects checkouts by payment status and age instead.
configure(
    django_host(
        production_packages={"saleor", "django"},
        publication_breaker=celery_publication_breaker,
        lifecycle_proofs=False,
    )
)
