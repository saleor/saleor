from __future__ import unicode_literals

import celery
import pytest


@celery.shared_task
def dummy_task(x):
    return x+1


@pytest.mark.integration
def test_task_running_asynchronously_on_worker(celery_worker):
    assert dummy_task.delay(42).get(timeout=10) == 43
