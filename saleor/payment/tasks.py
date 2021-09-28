from celery.utils.log import get_task_logger

from saleor.payment import gateway

from ..celeryconf import app
from ..plugins.manager import get_plugins_manager
from .models import Payment
from .utils import ReleasePaymentException, get_unfinished_payments

task_logger = get_task_logger(__name__)


@app.task
def release_unfinished_payments_task():
    payments = get_unfinished_payments()

    for payment in payments.iterator():
        payment.is_active = False
        payment.save(update_fields=["is_active", "modified"])
        refund_or_void_inactive_payment.delay(payment.pk)


@app.task(
    autoretry_for=[ReleasePaymentException],
    default_retry_delay=4 * 3600,  # 4 hours
    retry_kwargs={"max_retries": 6},
)
def refund_or_void_inactive_payment(payment_pk):
    payment = Payment.objects.get(pk=payment_pk)

    checkout = payment.checkout
    if checkout:
        channel_slug = checkout.channel.slug
    else:
        task_logger.warning("Payment %d has no checkout.", payment.pk)
        order = payment.order
        if order:
            channel_slug = order.channel.slug
        else:
            task_logger.error("Payment %d has no checkout and no order.", payment.pk)
            return

    try:
        manager = get_plugins_manager()
        gateway.payment_refund_or_void(payment, manager, channel_slug)

    except ReleasePaymentException as e:
        task_logger.error("Release payment %d failed.", payment.pk, e)
        raise

    else:
        task_logger.info("Released payment %d.", payment.pk)
