import pytest

from saleor.order.emails import (
    send_order_confirmation, send_payment_confirmation)


@pytest.mark.integration
def test_email_sending_asynchronously(
        transactional_db, celery_app, celery_worker, order_with_lines):
    order = send_order_confirmation.delay(order_with_lines.pk)
    payment = send_payment_confirmation.delay(order_with_lines.pk)
    order.get()
    payment.get()
