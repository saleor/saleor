import datetime
import logging
from unittest import mock
from unittest.mock import call, patch

import pytest
from django.test import override_settings
from django.utils import timezone
from freezegun import freeze_time

from ...core.models import EventDelivery
from ...discount.models import VoucherCustomer
from ...warehouse.models import Allocation
from ...webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from .. import OrderEvents, OrderStatus
from ..actions import call_order_event, call_order_events
from ..models import Order, OrderEvent, get_order_number
from ..tasks import (
    _bulk_release_voucher_usage,
    delete_expired_orders_task,
    expire_orders_task,
    send_order_updated,
)


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
    order_1.created_at = now - datetime.timedelta(minutes=10)
    order_1.voucher_code = code.code
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - datetime.timedelta(minutes=10)
    order_2.voucher_code = code.code
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=10)
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
    order_1.created_at = now - datetime.timedelta(minutes=10)
    order_1.voucher_code = code.code
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - datetime.timedelta(minutes=10)
    order_2.voucher_code = code_percentage.code
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=10)
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
    order_2.created_at = now - datetime.timedelta(minutes=120)
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=120)
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
    order_1.created_at = now - datetime.timedelta(minutes=10)
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - datetime.timedelta(minutes=10)
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=10)
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
    order_1.created_at = now - datetime.timedelta(minutes=10)
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - datetime.timedelta(minutes=10)
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=10)
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
    order_2.created_at = now - datetime.timedelta(minutes=120)
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=120)
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


@patch(
    "saleor.order.tasks.call_order_events",
    wraps=call_order_events,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_expire_orders_task_do_not_call_sync_webhooks(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_events,
    setup_order_webhooks,
    order_list,
    channel_USD,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_EXPIRED,
        ]
    )

    channel_USD.expire_orders_after = 60
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.created_at = now
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.save()

    order_2 = order_list[1]
    order_2.created_at = now - datetime.timedelta(minutes=120)
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.save()

    order_3 = order_list[2]
    order_3.created_at = now - datetime.timedelta(minutes=120)
    order_3.status = OrderStatus.UNFULFILLED
    order_3.save()

    # when
    with django_capture_on_commit_callbacks(execute=True):
        expire_orders_task()

    # then
    order_expired_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_EXPIRED,
    )
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    order_deliveries = [order_updated_delivery, order_expired_delivery]

    mocked_send_webhook_request_async.assert_has_calls(
        [
            call(
                kwargs={"event_delivery_id": delivery.id},
                queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
                bind=True,
                retry_backoff=10,
                retry_kwargs={"max_retries": 5},
            )
            for delivery in order_deliveries
        ],
        any_order=True,
    )

    assert not mocked_send_webhook_request_sync.called
    assert wrapped_call_order_events.called


@freeze_time("2020-03-18 12:00:00")
def test_delete_expired_orders_task(order_list, allocations, channel_USD):
    # given
    channel_USD.delete_expired_orders_after = datetime.timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
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
    channel_USD.delete_expired_orders_after = datetime.timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now - datetime.timedelta(days=5)
    order_1.status = OrderStatus.EXPIRED
    order_1.channel = channel_PLN
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
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
    channel_USD.delete_expired_orders_after = datetime.timedelta()
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
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
    channel_USD.delete_expired_orders_after = datetime.timedelta(days=3)
    channel_USD.save()

    channel_PLN.delete_expired_orders_after = datetime.timedelta(days=5)
    channel_PLN.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now - datetime.timedelta(days=2)
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.channel = channel_PLN
    order_3.save()

    order_4 = order_3
    order_4.pk = None
    order_4.number = get_order_number()
    order_4.expired_at = now - datetime.timedelta(days=4)
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
    channel_USD.delete_expired_orders_after = datetime.timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.FULFILLED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
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
    channel_USD.delete_expired_orders_after = datetime.timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now - datetime.timedelta(days=2)
    order_1.status = OrderStatus.EXPIRED
    order_1.save()
    transaction_item_generator(order_id=order_1.pk)

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()
    transaction_item_generator(order_id=order_2.pk)

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()
    transaction_item_generator(order_id=order_3.pk)

    order_4 = payment_dummy.order
    order_4.expired_at = now - datetime.timedelta(days=4)
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
    channel_USD.delete_expired_orders_after = datetime.timedelta(days=3)
    channel_USD.save()

    now = timezone.now()
    order_1 = order_list[0]
    order_1.expired_at = now
    order_1.status = OrderStatus.EXPIRED
    order_1.save()

    order_2 = order_list[1]
    order_2.expired_at = now - datetime.timedelta(days=5)
    order_2.status = OrderStatus.EXPIRED
    order_2.save()

    order_3 = order_list[2]
    order_3.expired_at = now - datetime.timedelta(days=7)
    order_3.status = OrderStatus.EXPIRED
    order_3.save()

    # when
    delete_expired_orders_task()

    # then
    mocked_delay.assert_called_once_with()
    assert Order.objects.count() == 2


def test_bulk_release_voucher_usage_voucher_usage_mismatch(
    order_list, allocations, channel_USD, voucher_customer, caplog
):
    # We can have mismatch between `voucher.used` and number of order utilizing
    # the voucher. It can happen in following cases:
    # CASE 1:
    # 1. use channelUpdate mutation to set:
    #   a. include_draft_order_in_voucher_usage=True
    #   b. automatically_confirm_all_new_orders=False
    # 2. create voucher with usageLimit=5
    # 3. create voucher code (let me name it code-123 for reference)
    # 4. create draft order and associate it with the code-123
    # State 1: Now we have draft order where
    # order.voucher_code=code-123 and voucher_code.used=1
    # 5. use channelUpdate mutation to set include_draft_order_in_voucher_usage=False.
    # It will decrease the voucher_code.used, but won’t disconnect voucher from
    # the orders
    # State 2: Now we have draft order where
    # order.voucher_code=code-123 and voucher_code.used=0
    #
    # CASE 2:
    # 1. use channelUpdate mutation to set:
    #   a. include_draft_order_in_voucher_usage=True
    #   b. automatically_confirm_all_new_orders=False
    # 2. create voucher without setting usage_limit
    # 3. create new code for the voucher (ie. code-123)
    # 4. create draft order and associate it with the “code-123”
    # 5. set usageLimit for the voucher
    # Now we have draft order where order.voucher_code=code-123 and voucher_code.used=0
    #
    # This test will mimic above steps to create the mismatch and will test
    # _bulk_release_voucher_usage trying to not save negative values

    # given
    channel_USD.expire_orders_after = 1
    channel_USD.save()

    now = timezone.now()
    caplog.set_level(logging.ERROR)
    code = voucher_customer.voucher_code
    voucher = code.voucher
    code.used = 1
    voucher.usage_limit = 3
    code.save(update_fields=["used"])
    voucher.save(update_fields=["usage_limit"])

    order_1 = order_list[0]
    order_1.status = OrderStatus.UNCONFIRMED
    order_1.created_at = now - datetime.timedelta(minutes=10)
    order_1.voucher_code = code.code
    order_1.save()

    order_2 = order_list[1]
    order_2.status = OrderStatus.UNCONFIRMED
    order_2.created_at = now - datetime.timedelta(minutes=10)
    order_2.voucher_code = code.code
    order_2.save()

    # when
    _bulk_release_voucher_usage([order_1.pk, order_2.pk])

    # then
    code.refresh_from_db()
    assert code.used == 0
    assert code.code in caplog.text


@patch(
    "saleor.order.tasks.call_order_event",
    wraps=call_order_event,
)
@patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
@override_settings(PLUGINS=["saleor.plugins.webhook.plugin.WebhookPlugin"])
def test_send_order_updated(
    mocked_send_webhook_request_async,
    mocked_send_webhook_request_sync,
    wrapped_call_order_event,
    setup_order_webhooks,
    order_with_lines,
    settings,
    django_capture_on_commit_callbacks,
):
    # given
    mocked_send_webhook_request_sync.return_value = []
    (
        tax_webhook,
        shipping_filter_webhook,
        additional_order_webhook,
    ) = setup_order_webhooks(
        [
            WebhookEventAsyncType.ORDER_UPDATED,
            WebhookEventAsyncType.ORDER_FULLY_PAID,
        ]
    )
    order = order_with_lines
    order.status = OrderStatus.UNCONFIRMED
    order.should_refresh_prices = True
    order.save(
        update_fields=[
            "status",
            "should_refresh_prices",
        ]
    )

    # when
    with django_capture_on_commit_callbacks(execute=True):
        send_order_updated([order.pk])

    # then
    # confirm that event delivery was generated for each async webhook.
    order_updated_delivery = EventDelivery.objects.get(
        webhook_id=additional_order_webhook.id,
        event_type=WebhookEventAsyncType.ORDER_UPDATED,
    )
    mocked_send_webhook_request_async.assert_called_once_with(
        kwargs={"event_delivery_id": order_updated_delivery.id},
        queue=settings.ORDER_WEBHOOK_EVENTS_CELERY_QUEUE_NAME,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )

    # confirm each sync webhook was called without saving event delivery
    assert mocked_send_webhook_request_sync.call_count == 2
    assert not EventDelivery.objects.exclude(
        webhook_id=additional_order_webhook.id
    ).exists()

    tax_delivery_call, filter_shipping_call = (
        mocked_send_webhook_request_sync.mock_calls
    )

    tax_delivery = tax_delivery_call.args[0]
    assert tax_delivery.webhook_id == tax_webhook.id

    filter_shipping_delivery = filter_shipping_call.args[0]
    assert filter_shipping_delivery.webhook_id == shipping_filter_webhook.id
    assert (
        filter_shipping_delivery.event_type
        == WebhookEventSyncType.ORDER_FILTER_SHIPPING_METHODS
    )

    assert wrapped_call_order_event.called
