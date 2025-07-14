import datetime
from decimal import Decimal
from unittest import mock

from freezegun import freeze_time

from ...checkout import CheckoutAuthorizeStatus, CheckoutChargeStatus
from ...checkout.actions import transaction_amounts_for_checkout_updated
from .. import TransactionAction, TransactionEventType
from ..tasks import (
    transaction_release_funds_for_checkout_task,
    transactions_to_release_funds,
)


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_checkout_with_new_last_change(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_before_ttl = ttl_time + datetime.timedelta(seconds=1)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )

    with freeze_time(time_before_ttl):
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_checkout_not_refundable(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = False
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_checkout_with_new_tr_modified(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_before_ttl = ttl_time + datetime.timedelta(seconds=1)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_before_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )

    with freeze_time(time_after_ttl):
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_checkout_with_none_status(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=0,
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert checkout.authorize_status == CheckoutAuthorizeStatus.NONE
    assert checkout.charge_status == CheckoutChargeStatus.NONE
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is True


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_not_valid_checkout(
    mocked_refund_action,
    mocked_cancel_action,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item_generator(
            charged_value=Decimal(100),
        )

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_transaction_for_order(
    mocked_refund_action,
    mocked_cancel_action,
    order,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item_generator(
            order_id=order.pk,
            charged_value=Decimal(100),
        )

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_without_transaction(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        checkout.authorize_status = CheckoutAuthorizeStatus.FULL
        checkout.charge_status = CheckoutChargeStatus.FULL
        checkout.automatically_refundable = True
        checkout.save(
            update_fields=[
                "automatically_refundable",
                "last_change",
                "authorize_status",
                "charge_status",
            ]
        )

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_refund_already_requested(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
            last_refund_success=False,
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])
    transaction_item.events.create(type=TransactionEventType.REFUND_REQUEST)

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_cancel_already_requested(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            authorized_value=Decimal(100),
            last_refund_success=False,
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])
    transaction_item.events.create(type=TransactionEventType.CANCEL_REQUEST)

    # when
    transaction_release_funds_for_checkout_task()

    # then
    assert not mocked_refund_action.called
    assert not mocked_cancel_action.called
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_transaction_with_authorization(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            authorized_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transaction_release_funds_for_checkout_task()

    # then
    request_event = transaction_item.events.filter(
        type=TransactionEventType.CANCEL_REQUEST
    ).first()
    assert request_event
    assert not mocked_refund_action.called
    mocked_cancel_action.assert_called_once_with(
        channel_slug=checkout.channel.slug,
        user=None,
        app=None,
        transaction=transaction_item,
        manager=mock.ANY,
        request_event=request_event,
        cancel_value=transaction_item.authorized_value,
        action=TransactionAction.CANCEL,
    )
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False


@mock.patch("saleor.payment.tasks.request_cancelation_action")
@mock.patch("saleor.payment.tasks.request_refund_action")
@freeze_time("2021-03-18 12:00:00")
def test_transaction_release_funds_for_checkout_task_transaction_with_charge(
    mocked_refund_action,
    mocked_cancel_action,
    checkout,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = True
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transaction_release_funds_for_checkout_task()

    # then
    request_event = transaction_item.events.filter(
        type=TransactionEventType.REFUND_REQUEST
    ).first()
    assert request_event
    assert not mocked_cancel_action.called
    mocked_refund_action.assert_called_once_with(
        channel_slug=checkout.channel.slug,
        user=None,
        app=None,
        transaction=transaction_item,
        manager=mock.ANY,
        request_event=request_event,
        refund_value=transaction_item.charged_value,
    )
    transaction_item.refresh_from_db()
    assert transaction_item.last_refund_success is False


@freeze_time("2021-03-18 12:00:00")
def test_transactions_to_release_funds_setting_toogle(
    channel_USD,
    channel_JPY,
    checkout,
    checkout_JPY,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    channel_USD.release_funds_for_expired_checkouts = False
    channel_USD.save()
    channel_JPY.release_funds_for_expired_checkouts = True
    channel_JPY.save()

    ttl_time = datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(hours=6)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transactions_for_checkout = {}
        for current_checkout in (checkout, checkout_JPY):
            transaction_item = transaction_item_generator(
                checkout_id=current_checkout.pk,
                charged_value=Decimal(100),
                currency=current_checkout.channel.currency_code,
            )
            transaction_amounts_for_checkout_updated(
                transaction_item, plugins_manager, user=None, app=None
            )
            current_checkout.automatically_refundable = True
            current_checkout.save(
                update_fields=["automatically_refundable", "last_change"]
            )
            transactions_for_checkout[current_checkout.pk] = transaction_item

    # when
    transactions = transactions_to_release_funds()

    # then
    assert len(transactions) == 1
    assert transactions[0].id == transactions_for_checkout[checkout_JPY.pk].id


@freeze_time("2021-03-18 12:00:00")
def test_transactions_to_release_funds_after_year(
    channel_USD,
    checkout,
    checkout_JPY,
    settings,
    transaction_item_generator,
    plugins_manager,
):
    # given
    ttl_time = datetime.datetime.now(tz=datetime.UTC)
    time_after_ttl = ttl_time - datetime.timedelta(seconds=1)
    with freeze_time(time_after_ttl):
        transaction_item = transaction_item_generator(
            checkout_id=checkout.pk,
            charged_value=Decimal(100),
        )
        transaction_amounts_for_checkout_updated(
            transaction_item, plugins_manager, user=None, app=None
        )
        checkout.automatically_refundable = True
        checkout.created_at = ttl_time - datetime.timedelta(days=366)
        checkout.save(update_fields=["automatically_refundable", "last_change"])

    # when
    transactions = transactions_to_release_funds()

    # then
    assert len(transactions) == 0
