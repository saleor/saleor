from __future__ import unicode_literals

import celery
import pytest
import mock
from saleor.order.emails import (send_order_confirmation,
                                 send_payment_confirmation)


@celery.shared_task
def dummy_task(x):
    return x+1


@pytest.mark.integration
def test_task_running_asynchronously_on_worker(celery_worker):
    assert dummy_task.delay(42).get(timeout=10) == 43


@pytest.mark.django_db
@pytest.mark.integration
@mock.patch('saleor.order.emails.send_templated_mail')
def test_email_sending_asynchronously(email_send, transactional_db, celery_app,
                                      celery_worker):
    order = send_order_confirmation.delay('joe.doe@foo.com', '/nowhere/to/go')
    payment = send_payment_confirmation.delay('joe.doe@foo.com', '/nowhere/')
    order.get()
    payment.get()
