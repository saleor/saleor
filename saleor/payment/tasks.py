from celery.utils.log import get_task_logger

from ..celeryconf import app
from ..plugins.manager import get_plugins_manager
from .models import Payment
from .utils import (
    ReleasePaymentException,
    get_unfinished_payments,
    release_checkout_payment,
)

task_logger = get_task_logger(__name__)


@app.task
def release_unfinished_payments_task():
    payments = get_unfinished_payments()

    for payment in payments.iterator():
        release_dangling_unfinished_payment_task.delay(payment.pk)


@app.task(
    autoretry_for=(ReleasePaymentException,),
    default_retry_delay=3 * 3600,  # 3 hours
    retry_kwargs={"max_retries": 3},
)
def release_dangling_unfinished_payment_task(pk):
    payment = Payment.objects.get(pk=pk)
    manager = get_plugins_manager()

    try:
        release_checkout_payment(payment, manager)
    except ReleasePaymentException as e:
        task_logger.error("Release payment %d failed.", payment.pk, e)
        raise
    else:
        task_logger.info("Released payment %d.", payment.pk)
