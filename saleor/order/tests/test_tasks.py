from datetime import timedelta
from unittest import mock
from unittest.mock import patch

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ...discount.models import VoucherCustomer
from ...warehouse.models import Allocation
from .. import OrderEvents, OrderStatus
from ..models import Order, OrderEvent, get_order_number
from ..tasks import delete_expired_orders_task, expire_orders_task


def test_expire_orders_task_check_voucher(
    order_list, allocations, channel_USD, voucher_customer
):
    # given
    channel_USD.expire_orders_after = 1
    channel_USD.save()

    now = timezone.now()
    code = voucher_customer.voucher_code
    voucher = voucher_customer.voucher_code.voucher
    code.used = 3
    code.voucher.usage_limit = 3
    code.save(update_fields=["used"])
    voucher.save(update_fields=["usage_limit"])

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.created_at = now - timezone.timedelta(minutes=10)
    order_1.voucher_code = code.code
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - timezone.timedelta(minutes=10)
    order_2.voucher_code = code.code
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=10)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.voucher_code = code.code
    order_3.save()

    # when
    expire_orders_task()

    # then
    for order in order_list:
        order.refresh_from_db()
    assert order_1.status == OrderStatus.EXPIRED
    assert order_2.status == OrderStatus.EXPIRED
    assert order_3.status == OrderStatus.UNFULFILLED

    assert not Allocation.objects.filter(
        order_line__order=order_1, quantity_allocated__gt=0
    ).exists()
    assert not Allocation.objects.filter(
        order_line__order=order_2, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_3, quantity_allocated__gt=0
    ).exists()

    code.refresh_from_db()
    assert code.used == 1
    assert not VoucherCustomer.objects.filter(pk=voucher_customer.pk).exists()


def test_expire_orders_task_check_multiple_vouchers(
    order_list,
    allocations,
    channel_USD,
    voucher,
    voucher_percentage,
):
    # given
    channel_USD.expire_orders_after = 1
    channel_USD.save()

    now = timezone.now()
    code = voucher.codes.first()
    code.used = 2
    code.save()
    voucher.usage_limit = 2
    voucher.save()
    code_percentage = voucher_percentage.codes.first()
    code_percentage.used = 1
    code_percentage.save()
    voucher_percentage.usage_limit = 1
    voucher_percentage.save()

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.created_at = now - timezone.timedelta(minutes=10)
    order_1.voucher_code = code.code
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - timezone.timedelta(minutes=10)
    order_2.voucher_code = code_percentage.code
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=10)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.voucher_code = code.code
    order_3.save()

    # when
    expire_orders_task()

    # then
    for order in order_list:
        order.refresh_from_db()
    assert order_1.status == OrderStatus.EXPIRED
    assert order_2.status == OrderStatus.EXPIRED
    assert order_3.status == OrderStatus.UNFULFILLED

    assert not Allocation.objects.filter(
        order_line__order=order_1, quantity_allocated__gt=0
    ).exists()
    assert not Allocation.objects.filter(
        order_line__order=order_2, quantity_allocated__gt=0
    ).exists()
    assert Allocation.objects.filter(
        order_line__order=order_3, quantity_allocated__gt=0
    ).exists()

    code.refresh_from_db()
    assert code.used == 1
    code_percentage.refresh_from_db()
    assert code_percentage.used == 0


def test_expire_orders_task_creates_order_events(order_list, allocations, channel_USD):
    # given
    channel_USD.expire_orders_after = 60
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.created_at = now
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.save()

    order_2 = order_list[1]
    order_2.created_at = now - timezone.timedelta(minutes=120)
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=120)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.save()

    # when
    expire_orders_task()

    # then
    for order in order_list:
        order.refresh_from_db()
    assert order_1.status == OrderStatus.UNCONFIRMED
    assert order_2.status == OrderStatus.EXPIRED
    assert order_3.status == OrderStatus.UNFULFILLED

    assert not OrderEvent.objects.filter(
        order_id=order_1.pk,
        type=OrderEvents.EXPIRED,
    ).exists()
    assert OrderEvent.objects.filter(
        order_id=order_2.pk,
        type=OrderEvents.EXPIRED,
    ).exists()
    assert not OrderEvent.objects.filter(
        order_id=order_3.pk,
        type=OrderEvents.EXPIRED,
    ).exists()


def test_expire_orders_task_with_transaction_item(
    order_list,
    transaction_item,
    allocations,
    channel_USD,
):
    # given
    channel_USD.expire_orders_after = 1
    channel_USD.save()

    now = timezone.now()

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.created_at = now - timezone.timedelta(minutes=10)
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - timezone.timedelta(minutes=10)
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=10)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.save()

    transaction_item.order_id = order_2.pk
    transaction_item.save()

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


def test_expire_orders_task_with_payment(
    order_list,
    payment_dummy,
    allocations,
    channel_USD,
):
    # given
    channel_USD.expire_orders_after = 1
    channel_USD.save()

    now = timezone.now()

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.created_at = now - timezone.timedelta(minutes=10)
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - timezone.timedelta(minutes=10)
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=10)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.save()

    payment_dummy.order_id = order_2.pk
    payment_dummy.save()

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


@pytest.mark.parametrize("expire_after", [None, 0, -1])
def test_expire_orders_task_none_expiration_time(
    expire_after,
    order_list,
    allocations,
    channel_USD,
):
    # given
    channel_USD.expire_orders_after = expire_after
    channel_USD.save()

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.save()

    order_3 = order_list[2]
    order_3.status = OrderStatus.UNFULFILLED
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
    order_1.save()

    order_2 = order_list[1]
    order_2.created_at = now - timezone.timedelta(minutes=120)
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - timezone.timedelta(minutes=120)
    order_3.status = OrderStatus.UNFULFILLED
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


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task(order_list, allocations, channel_USD):
    # given
    channel_USD.delete_expired_orders_after = timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()

    # when
    delete_expired_orders_task()

    # then
    assert Order.objects.count() == 1
    assert order_1.id == Order.objects.get().id


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task_multiple_channels_one_without_delete(
    order_list, allocations, channel_USD, channel_PLN
):
    # given
    channel_USD.delete_expired_orders_after = timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now - timedelta(days=5)
    order_1.status = OrderStatus.EXPIRED
    order_1.channel = channel_PLN
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()

    # when
    delete_expired_orders_task()

    # then
    assert Order.objects.count() == 1
    assert order_1.id == Order.objects.get().id


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task_channel_without_delete(
    order_list, allocations, channel_USD
):
    # given
    channel_USD.delete_expired_orders_after = timedelta()
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()

    # when
    delete_expired_orders_task()

    # then
    assert Order.objects.count() == 3


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task_multiple_channels_with_different_deletion_time(
    order_list, allocations, channel_USD, channel_PLN
):
    # given
    channel_USD.delete_expired_orders_after = timedelta(days=3)
    channel_USD.save()

    channel_PLN.delete_expired_orders_after = timedelta(days=5)
    channel_PLN.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now - timedelta(days=2)
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.channel = channel_PLN
    order_3.save()

    order_4 = order_3
    order_4.pk = None
    order_4.number = get_order_number()
    order_4.expired_at = now - timedelta(days=4)
    order_4.status = OrderStatus.EXPIRED
    order_4.channel = channel_PLN
    order_4.save()

    # when
    delete_expired_orders_task()

    # then
    assert Order.objects.count() == 2
    assert Order.objects.filter(id=order_1.pk)
    assert Order.objects.filter(id=order_4.pk)


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task_orders_with_different_status_than_expired(
    order_list, allocations, channel_USD
):
    # given
    channel_USD.delete_expired_orders_after = timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.FULFILLED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.RETURNED
    order_3.save()

    # when
    delete_expired_orders_task()

    # then
    assert Order.objects.count() == 3


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task_orders_with_payment_objects(
    order_list, payment_dummy, transaction_item_generator, allocations, channel_USD
):
    # given
    channel_USD.delete_expired_orders_after = timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now - timedelta(days=2)
    order_1.status = OrderStatus.EXPIRED
    order_1.save()
    transaction_item_generator(order_id=order_1.pk)

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()
    transaction_item_generator(order_id=order_2.pk)

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()
    transaction_item_generator(order_id=order_3.pk)

    order_4 = payment_dummy.order
    order_4.expired_at = now - timedelta(days=4)
    order_4.status = OrderStatus.EXPIRED
    order_4.save()

    # when
    delete_expired_orders_task()

    # then
    assert Order.objects.count() == 4


@mock.patch("saleor.order.tasks.DELETE_EXPIRED_ORDER_BATCH_SIZE", 1)
@patch("saleor.order.tasks.delete_expired_orders_task.delay")
def test_delete_expired_orders_task_schedule_itself(
    mocked_delay, order_list, allocations, channel_USD
):
    # given
    channel_USD.delete_expired_orders_after = timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()

    # when
    delete_expired_orders_task()

    # then
    mocked_delay.assert_called_once_with()
    assert Order.objects.count() == 2
