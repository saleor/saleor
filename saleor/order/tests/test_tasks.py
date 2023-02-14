from decimal import Decimal
from unittest.mock import patch

from django.utils import timezone

from ...core.models import CeleryTask
from ...discount.models import VoucherCustomer
from ...warehouse.models import Allocation
from .. import OrderStatus
from ..tasks import expire_orders_task


def test_expire_orders_task(order_list, allocations, channel_USD, voucher_customer):
    # given
    channel_USD.expire_orders_after = 0
    channel_USD.save()

    voucher = voucher_customer.voucher
    voucher.used = 3
    voucher.usage_limit = 3
    voucher.save()

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.total_charged_amount = Decimal(0)
    order_1.voucher = voucher
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.total_charged_amount = Decimal(10)
    order_1.voucher = voucher
    order_2.save()

    order_3 = order_list[2]
    order_3.status = OrderStatus.UNFULFILLED
    order_3.total_charged_amount = Decimal(0)
    order_1.voucher = voucher
    order_3.save()

    # when
    expire_orders_task()

    # then
    for order in order_list:
        order.refresh_from_db()
    assert order_1.status == OrderStatus.EXPIRED
    assert order_2.status == OrderStatus.UNCONFIRMED
    assert order_3.status == OrderStatus.UNFULFILLED

    assert not Allocation.objects.filter(
        order_line__order=order_1, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_2, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_3, quantity_allocated__gt=0
    ).exists()

    voucher.refresh_from_db()
    assert voucher.used == 2
    assert not VoucherCustomer.objects.filter(pk=voucher_customer.pk).exists()


def test_expire_orders_task_none_expiration_time(order_list, allocations, channel_USD):
    # given
    channel_USD.expire_orders_after = None
    channel_USD.save()

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.total_charged_amount = Decimal(0)
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.total_charged_amount = Decimal(0)
    order_2.save()

    order_3 = order_list[2]
    order_3.status = OrderStatus.UNFULFILLED
    order_3.total_charged_amount = Decimal(0)
    order_3.save()

    # when
    expire_orders_task()

    # then
    for order in order_list:
        order.refresh_from_db()
    assert order_1.status == OrderStatus.UNCONFIRMED
    assert order_2.status == OrderStatus.UNCONFIRMED
    assert order_3.status == OrderStatus.UNFULFILLED

    assert Allocation.objects.filter(
        order_line__order=order_1, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_2, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_3, quantity_allocated__gt=0
    ).exists()


def test_expire_orders_task_after(order_list, allocations, channel_USD):
    # given
    channel_USD.expire_orders_after = 60
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.created_at = now
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.total_charged_amount = Decimal(0)
    order_1.save()

    order_2 = order_list[1]
    order_2.created_at = now - timezone.timedelta(minutes=120)
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.total_charged_amount = Decimal(0)
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=120)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.total_charged_amount = Decimal(0)
    order_3.save()

    # when
    expire_orders_task()

    # then
    for order in order_list:
        order.refresh_from_db()
    assert order_1.status == OrderStatus.UNCONFIRMED
    assert order_2.status == OrderStatus.EXPIRED
    assert order_3.status == OrderStatus.UNFULFILLED

    assert Allocation.objects.filter(
        order_line__order=order_1, quantity_allocated__gt=0
    ).exists()
    assert not Allocation.objects.filter(
        order_line__order=order_2, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_3, quantity_allocated__gt=0
    ).exists()


@patch("logging.Logger.error")
def test_expire_orders_task_locked_over_hour(logger_mock, order_list, allocations):
    # given
    task_name = "expire_orders"
    error_msg = "%s task exceeded 1h working time."

    now = timezone.now()

    lock = CeleryTask.objects.create(name=task_name)
    lock.created_at = now - timezone.timedelta(hours=2)
    lock.save()

    # when
    expire_orders_task()

    # then
    logger_mock.assert_called_once_with(error_msg, [task_name])
