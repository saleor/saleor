import json
from datetime import date, timedelta
from unittest.mock import patch

import graphene
import pytest
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from freezegun import freeze_time

from ...core import TimePeriodType
from ...core.exceptions import GiftCardNotApplicable
from ...core.utils.json_serializer import CustomJsonEncoder
from ...core.utils.promo_code import InvalidPromoCode
from ...order.models import OrderLine
from ...plugins.manager import get_plugins_manager
from ...site import GiftCardSettingsExpiryType
from ...tests.utils import flush_post_commit_hooks
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.payloads import generate_meta, generate_requestor
from .. import GiftCardEvents, GiftCardLineData, events
from ..models import GiftCard, GiftCardEvent
from ..utils import (
    add_gift_card_code_to_checkout,
    assign_user_gift_cards,
    calculate_expiry_date,
    deactivate_order_gift_cards,
    fulfill_gift_card_lines,
    fulfill_non_shippable_gift_cards,
    get_gift_card_lines,
    get_non_shippable_gift_card_lines,
    gift_cards_create,
    is_gift_card_expired,
    order_has_gift_card_lines,
    remove_gift_card_code_from_checkout,
)


def test_add_gift_card_code_to_checkout(checkout, gift_card):
    # given
    assert checkout.gift_cards.count() == 0

    # when
    add_gift_card_code_to_checkout(
        checkout, "test@example.com", gift_card.code, gift_card.currency
    )

    # then
    assert checkout.gift_cards.count() == 1


def test_add_gift_card_code_to_checkout_inactive_card(checkout, gift_card):
    # given
    gift_card.is_active = False
    gift_card.save(update_fields=["is_active"])

    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, "test@example.com", gift_card.code, gift_card.currency
        )


def test_add_gift_card_code_to_checkout_expired_card(checkout, gift_card):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=10)
    gift_card.save(update_fields=["expiry_date"])

    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, "test@example.com", gift_card.code, gift_card.currency
        )


def test_add_gift_card_code_to_checkout_invalid_currency(checkout, gift_card):
    # given
    currency = "EUR"

    assert gift_card.currency != currency
    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, "test@example.com", gift_card.code, currency
        )


def test_add_gift_card_code_to_checkout_used_gift_card(checkout, gift_card_used):
    # given
    assert gift_card_used.used_by_email
    assert checkout.gift_cards.count() == 0

    # when
    add_gift_card_code_to_checkout(
        checkout,
        gift_card_used.used_by_email,
        gift_card_used.code,
        gift_card_used.currency,
    )

    # then
    assert checkout.gift_cards.count() == 1


def test_add_gift_card_code_to_checkout_used_gift_card_invalid_user(
    checkout, gift_card_used
):
    # given
    email = "new_user@example.com"
    assert gift_card_used.used_by_email
    assert gift_card_used.used_by_email != email
    assert checkout.gift_cards.count() == 0

    # when
    # then
    with pytest.raises(InvalidPromoCode):
        add_gift_card_code_to_checkout(
            checkout, email, gift_card_used.code, gift_card_used.currency
        )


def test_remove_gift_card_code_from_checkout(checkout, gift_card):
    # given
    checkout.gift_cards.add(gift_card)
    assert checkout.gift_cards.count() == 1

    # when
    remove_gift_card_code_from_checkout(checkout, gift_card.code)

    # then
    assert checkout.gift_cards.count() == 0


def test_remove_gift_card_code_from_checkout_no_checkout_gift_cards(
    checkout, gift_card
):
    # given
    assert checkout.gift_cards.count() == 0

    # when
    remove_gift_card_code_from_checkout(checkout, gift_card.code)

    # then
    assert checkout.gift_cards.count() == 0


@pytest.mark.parametrize(
    "period_type, period", [("years", 5), ("weeks", 1), ("months", 13), ("days", 100)]
)
def test_calculate_expiry_settings(period_type, period, site_settings):
    # given
    site_settings.gift_card_expiry_type = GiftCardSettingsExpiryType.EXPIRY_PERIOD
    site_settings.gift_card_expiry_period_type = period_type.rstrip("s")
    site_settings.gift_card_expiry_period = period
    site_settings.save(
        update_fields=[
            "gift_card_expiry_type",
            "gift_card_expiry_period_type",
            "gift_card_expiry_period",
        ]
    )

    # when
    expiry_date = calculate_expiry_date(site_settings)

    # then
    assert expiry_date == timezone.now().date() + relativedelta(**{period_type: period})


def test_calculate_expiry_settings_for_never_expire_settings(site_settings):
    # given
    site_settings.gift_card_expiry_type = GiftCardSettingsExpiryType.NEVER_EXPIRE

    # when
    expiry_date = calculate_expiry_date(site_settings)

    # then
    assert expiry_date is None


@patch("saleor.giftcard.utils.send_gift_card_notification")
def test_gift_cards_create(
    send_notification_mock,
    order,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
    site_settings,
    staff_user,
):
    # given
    manager = get_plugins_manager()
    line_1, line_2 = gift_card_shippable_order_line, gift_card_non_shippable_order_line
    user_email = order.user_email
    fulfillment = order.fulfillments.create(tracking_number="123")
    fulfillment_line_1 = fulfillment.lines.create(
        order_line=line_1,
        quantity=line_1.quantity,
        stock=line_1.allocations.get().stock,
    )
    fulfillment_line_2 = fulfillment.lines.create(
        order_line=line_2,
        quantity=line_2.quantity,
        stock=line_2.allocations.get().stock,
    )
    lines_data = [
        GiftCardLineData(
            quantity=1,
            order_line=line_1,
            variant=line_1.variant,
            fulfillment_line=fulfillment_line_1,
        ),
        GiftCardLineData(
            quantity=1,
            order_line=line_2,
            variant=line_2.variant,
            fulfillment_line=fulfillment_line_2,
        ),
    ]

    # when
    gift_cards = gift_cards_create(
        order, lines_data, site_settings, staff_user, None, manager
    )

    # then
    assert len(gift_cards) == len(lines_data)

    shippable_gift_card = gift_cards[0]
    shippable_price = gift_card_shippable_order_line.unit_price_gross
    assert shippable_gift_card.initial_balance == shippable_price
    assert shippable_gift_card.current_balance == shippable_price
    assert shippable_gift_card.created_by == order.user
    assert shippable_gift_card.created_by_email == user_email
    assert shippable_gift_card.expiry_date is None
    assert shippable_gift_card.fulfillment_line == fulfillment_line_1

    bought_event_for_shippable_card = GiftCardEvent.objects.get(
        gift_card=shippable_gift_card
    )
    assert bought_event_for_shippable_card.user == staff_user
    assert bought_event_for_shippable_card.app is None
    assert bought_event_for_shippable_card.type == GiftCardEvents.BOUGHT
    assert bought_event_for_shippable_card.order == order
    assert bought_event_for_shippable_card.parameters == {
        "expiry_date": None,
    }

    non_shippable_gift_card = gift_cards[1]
    non_shippable_price = gift_card_non_shippable_order_line.total_price_gross
    assert non_shippable_gift_card.initial_balance == non_shippable_price
    assert non_shippable_gift_card.current_balance == non_shippable_price
    assert non_shippable_gift_card.created_by == order.user
    assert non_shippable_gift_card.created_by_email == user_email
    assert non_shippable_gift_card.expiry_date is None
    assert non_shippable_gift_card.fulfillment_line == fulfillment_line_2

    non_shippable_event = GiftCardEvent.objects.get(
        gift_card=non_shippable_gift_card, type=GiftCardEvents.BOUGHT
    )
    assert non_shippable_event.user == staff_user
    assert non_shippable_event.app is None
    assert non_shippable_event.order == order
    assert non_shippable_event.parameters == {
        "expiry_date": None,
    }

    flush_post_commit_hooks()

    send_notification_mock.assert_called_once_with(
        staff_user,
        None,
        order.user,
        user_email,
        non_shippable_gift_card,
        manager,
        order.channel.slug,
        resending=False,
    )


@patch("saleor.giftcard.utils.send_gift_card_notification")
def test_gift_cards_create_expiry_date_set(
    send_notification_mock,
    order,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
    site_settings,
    staff_user,
):
    # given
    manager = get_plugins_manager()
    site_settings.gift_card_expiry_type = GiftCardSettingsExpiryType.EXPIRY_PERIOD
    site_settings.gift_card_expiry_period_type = TimePeriodType.WEEK
    site_settings.gift_card_expiry_period = 20
    site_settings.save(
        update_fields=[
            "gift_card_expiry_type",
            "gift_card_expiry_period_type",
            "gift_card_expiry_period",
        ]
    )
    line_1 = gift_card_non_shippable_order_line
    user_email = order.user_email
    fulfillment = order.fulfillments.create(tracking_number="123")
    fulfillment_line_1 = fulfillment.lines.create(
        order_line=line_1,
        quantity=line_1.quantity,
        stock=line_1.allocations.get().stock,
    )
    lines_data = [
        GiftCardLineData(
            quantity=1,
            order_line=line_1,
            variant=line_1.variant,
            fulfillment_line=fulfillment_line_1,
        )
    ]

    # when
    gift_cards = gift_cards_create(
        order, lines_data, site_settings, staff_user, None, manager
    )

    # then
    assert len(gift_cards) == len(lines_data)

    gift_card = gift_cards[0]
    price = gift_card_non_shippable_order_line.total_price_gross
    assert gift_card.initial_balance == price
    assert gift_card.current_balance == price
    assert gift_card.created_by == order.user
    assert gift_card.created_by_email == user_email
    assert gift_card.expiry_date
    assert gift_card.fulfillment_line == fulfillment_line_1

    event = GiftCardEvent.objects.get(gift_card=gift_card, type=GiftCardEvents.BOUGHT)
    assert event.user == staff_user
    assert event.app is None
    assert event.order == order
    assert event.parameters == {
        "expiry_date": gift_card.expiry_date.isoformat(),
    }

    flush_post_commit_hooks()

    send_notification_mock.assert_called_once_with(
        staff_user,
        None,
        order.user,
        user_email,
        gift_card,
        manager,
        order.channel.slug,
        resending=False,
    )


@patch("saleor.giftcard.utils.send_gift_card_notification")
def test_gift_cards_create_multiple_quantity(
    send_notification_mock,
    order,
    gift_card_non_shippable_order_line,
    site_settings,
    staff_user,
):
    # given
    manager = get_plugins_manager()
    quantity = 3
    gift_card_non_shippable_order_line.quantity = quantity
    gift_card_non_shippable_order_line.save(update_fields=["quantity"])
    fulfillment = order.fulfillments.create(tracking_number="123")
    stock = gift_card_non_shippable_order_line.allocations.get().stock
    fulfillment_line = fulfillment.lines.create(
        order_line=gift_card_non_shippable_order_line, quantity=quantity, stock=stock
    )
    lines_data = [
        GiftCardLineData(
            quantity=quantity,
            order_line=gift_card_non_shippable_order_line,
            variant=gift_card_non_shippable_order_line.variant,
            fulfillment_line=fulfillment_line,
        )
    ]

    # when
    gift_cards = gift_cards_create(
        order, lines_data, site_settings, staff_user, None, manager
    )

    # then
    flush_post_commit_hooks()
    assert len(gift_cards) == quantity
    price = gift_card_non_shippable_order_line.unit_price_gross
    for gift_card in gift_cards:
        assert gift_card.initial_balance == price
        assert gift_card.current_balance == price
        assert gift_card.fulfillment_line == fulfillment_line

    assert GiftCardEvent.objects.filter(type=GiftCardEvents.BOUGHT).count() == quantity
    assert send_notification_mock.call_count == quantity


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
@patch("saleor.giftcard.utils.send_gift_card_notification")
def test_gift_cards_create_trigger_webhook(
    send_notification_mock,
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    webhook_app,
    settings,
    order,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
    site_settings,
    staff_user,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    manager = get_plugins_manager()
    line_1, line_2 = gift_card_shippable_order_line, gift_card_non_shippable_order_line
    fulfillment = order.fulfillments.create(tracking_number="123")
    fulfillment_line_1 = fulfillment.lines.create(
        order_line=line_1,
        quantity=line_1.quantity,
        stock=line_1.allocations.get().stock,
    )
    fulfillment_line_2 = fulfillment.lines.create(
        order_line=line_2,
        quantity=line_2.quantity,
        stock=line_2.allocations.get().stock,
    )
    lines_data = [
        GiftCardLineData(
            quantity=1,
            order_line=line_1,
            variant=line_1.variant,
            fulfillment_line=fulfillment_line_1,
        ),
        GiftCardLineData(
            quantity=1,
            order_line=line_2,
            variant=line_2.variant,
            fulfillment_line=fulfillment_line_2,
        ),
    ]

    # when
    gift_cards = gift_cards_create(
        order, lines_data, site_settings, staff_user, None, manager
    )

    # then
    flush_post_commit_hooks()
    assert len(gift_cards) == len(lines_data)

    gift_card = gift_cards[-1]
    gift_card_global_id = graphene.Node.to_global_id("GiftCard", gift_card.id)

    mocked_webhook_trigger.assert_called_with(
        json.dumps(
            {
                "id": gift_card_global_id,
                "is_active": True,
                "meta": generate_meta(
                    requestor_data=generate_requestor(),
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.GIFT_CARD_CREATED,
        [any_webhook],
        gift_card,
        None,
    )

    send_notification_mock.assert_called()


def test_get_gift_card_lines(
    gift_card_non_shippable_order_line, gift_card_shippable_order_line, order_line
):
    # given
    lines = [
        gift_card_non_shippable_order_line,
        gift_card_shippable_order_line,
        order_line,
    ]

    # when
    gift_card_lines = get_gift_card_lines(lines)

    # then
    assert set(gift_card_lines) == {
        gift_card_non_shippable_order_line,
        gift_card_shippable_order_line,
    }


def test_get_gift_card_lines_no_gift_card_lines(
    order_line_with_one_allocation, order_line
):
    # given
    lines = [order_line_with_one_allocation, order_line]

    # when
    gift_card_lines = get_gift_card_lines(lines)

    # then
    assert not gift_card_lines


def test_get_non_shippable_gift_card_lines(
    gift_card_non_shippable_order_line, gift_card_shippable_order_line, order_line
):
    # given
    lines = [
        gift_card_non_shippable_order_line,
        gift_card_shippable_order_line,
        order_line,
    ]

    # when
    gift_card_lines = get_non_shippable_gift_card_lines(lines)

    # then
    assert set(gift_card_lines) == {gift_card_non_shippable_order_line}


def test_get_non_shippable_gift_card_lines_no_gift_card_lines(
    order_line_with_one_allocation, order_line
):
    # given
    lines = [order_line_with_one_allocation, order_line]

    # when
    gift_card_lines = get_gift_card_lines(lines)

    # then
    assert not gift_card_lines


@patch("saleor.giftcard.utils.create_fulfillments")
def test_fulfill_non_shippable_gift_cards(
    create_fulfillments_mock,
    order,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
    site_settings,
    staff_user,
    warehouse,
):
    # given
    manager = get_plugins_manager()
    order_lines = [gift_card_shippable_order_line, gift_card_non_shippable_order_line]

    # when
    fulfill_non_shippable_gift_cards(
        order, order_lines, site_settings, staff_user, None, manager
    )

    # then
    fulfillment_lines_for_warehouses = {
        warehouse.pk: [
            {
                "order_line": gift_card_non_shippable_order_line,
                "quantity": gift_card_non_shippable_order_line.quantity,
            },
        ]
    }

    create_fulfillments_mock.assert_called_once()
    args, kwargs = create_fulfillments_mock.call_args
    assert args[0] == staff_user
    assert args[1] is None
    assert args[2] == order
    assert args[3] == fulfillment_lines_for_warehouses
    assert args[4] == manager
    assert args[5] == site_settings
    assert kwargs["notify_customer"] is True


@patch("saleor.giftcard.utils.create_fulfillments")
def test_fulfill_non_shippable_gift_cards_line_with_allocation(
    create_fulfillments_mock,
    order,
    gift_card_shippable_order_line,
    gift_card_non_shippable_order_line,
    site_settings,
    staff_user,
    warehouse,
):
    # given
    manager = get_plugins_manager()
    order_lines = [gift_card_shippable_order_line, gift_card_non_shippable_order_line]

    order = gift_card_non_shippable_order_line.order
    non_shippable_variant = gift_card_non_shippable_order_line.variant
    non_shippable_variant.track_inventory = True
    non_shippable_variant.save(update_fields=["track_inventory"])

    stock = non_shippable_variant.stocks.first()

    # when
    fulfill_non_shippable_gift_cards(
        order, order_lines, site_settings, staff_user, None, manager
    )

    fulfillment_lines_for_warehouses = {
        stock.warehouse.pk: [
            {
                "order_line": gift_card_non_shippable_order_line,
                "quantity": gift_card_non_shippable_order_line.quantity,
            },
        ]
    }

    create_fulfillments_mock.assert_called_once()
    args, kwargs = create_fulfillments_mock.call_args
    assert args[0] == staff_user
    assert args[1] is None
    assert args[2] == order
    assert args[3] == fulfillment_lines_for_warehouses
    assert args[4] == manager
    assert args[5] == site_settings
    assert kwargs["notify_customer"] is True


def test_fulfill_gift_card_lines(
    staff_user,
    gift_card_non_shippable_order_line,
    gift_card_shippable_order_line,
    site_settings,
):
    # given
    manager = get_plugins_manager()
    order = gift_card_non_shippable_order_line.order
    non_shippable_variant = gift_card_non_shippable_order_line.variant
    non_shippable_variant.track_inventory = True
    non_shippable_variant.save(update_fields=["track_inventory"])

    lines = OrderLine.objects.filter(
        pk__in=[
            gift_card_non_shippable_order_line.pk,
            gift_card_shippable_order_line.pk,
        ]
    )

    # when
    fulfillments = fulfill_gift_card_lines(
        lines, staff_user, None, order, site_settings, manager
    )

    # then
    assert len(fulfillments) == 1
    assert fulfillments[0].lines.count() == len(lines)
    flush_post_commit_hooks()
    gift_cards = GiftCard.objects.all()
    assert gift_cards.count() == sum([line.quantity for line in lines])
    shippable_gift_cards = gift_cards.filter(
        product_id=gift_card_shippable_order_line.variant.product_id
    )
    assert len(shippable_gift_cards) == gift_card_shippable_order_line.quantity
    non_shippable_gift_cards = gift_cards.filter(
        product_id=gift_card_non_shippable_order_line.variant.product_id
    )
    assert len(non_shippable_gift_cards) == gift_card_non_shippable_order_line.quantity
    for card in gift_cards:
        assert card.initial_balance.amount == round(
            gift_card_non_shippable_order_line.unit_price_gross.amount, 2
        )
        assert card.current_balance.amount == round(
            gift_card_non_shippable_order_line.unit_price_gross.amount, 2
        )
        assert card.fulfillment_line
        assert GiftCardEvent.objects.filter(gift_card=card, type=GiftCardEvents.BOUGHT)


def test_fulfill_gift_card_lines_lack_of_stock(
    staff_user,
    gift_card_non_shippable_order_line,
    gift_card_shippable_order_line,
    site_settings,
):
    # given
    manager = get_plugins_manager()
    order = gift_card_non_shippable_order_line.order
    gift_card_non_shippable_order_line.variant.stocks.all().delete()

    lines = OrderLine.objects.filter(
        pk__in=[
            gift_card_non_shippable_order_line.pk,
            gift_card_shippable_order_line.pk,
        ]
    )

    # when
    with pytest.raises(GiftCardNotApplicable):
        fulfill_gift_card_lines(lines, staff_user, None, order, site_settings, manager)


def test_deactivate_order_gift_cards(
    gift_card, gift_card_expiry_date, gift_card_created_by_staff, order, staff_user
):
    # given
    bought_cards = [gift_card, gift_card_expiry_date]
    events.gift_cards_bought_event(bought_cards, order, staff_user, None)

    for card in [gift_card, gift_card_expiry_date, gift_card_created_by_staff]:
        assert card.is_active

    # when
    deactivate_order_gift_cards(order.id, staff_user, None)

    # then
    for card in bought_cards:
        card.refresh_from_db()
        assert not card.is_active
        assert card.events.filter(type=GiftCardEvents.DEACTIVATED)

    assert gift_card_created_by_staff.is_active
    assert not gift_card_created_by_staff.events.filter(type=GiftCardEvents.DEACTIVATED)


def test_deactivate_order_gift_cards_no_order_gift_cards(
    gift_card, gift_card_expiry_date, gift_card_created_by_staff, order, staff_user
):
    # given
    cards = [gift_card, gift_card_expiry_date, gift_card_created_by_staff]
    for card in cards:
        assert card.is_active

    # when
    deactivate_order_gift_cards(order.id, staff_user, None)

    # then
    for card in cards:
        card.refresh_from_db()
        assert card.is_active


def test_order_has_gift_card_lines_true(gift_card_shippable_order_line):
    order = gift_card_shippable_order_line.order
    assert order_has_gift_card_lines(order) is True


def test_order_has_gift_card_lines_false(order):
    assert order_has_gift_card_lines(order) is False


def test_assign_user_gift_cards(
    customer_user,
    gift_card,
    gift_card_expiry_date,
    gift_card_used,
    gift_card_created_by_staff,
):
    # given
    card_ids = [
        card.id
        for card in [
            gift_card,
            gift_card_expiry_date,
            gift_card_created_by_staff,
            gift_card_used,
        ]
    ]
    GiftCard.objects.filter(id__in=card_ids).update(created_by=None)

    gift_card_used.used_by = None
    gift_card_used.save(update_fields=["used_by"])

    # when
    assign_user_gift_cards(customer_user)

    # then
    for card in [gift_card, gift_card_expiry_date]:
        card.refresh_from_db()
        assert card.created_by == customer_user

    gift_card_used.refresh_from_db()
    assert gift_card_used.used_by == customer_user
    assert not gift_card_used.created_by


def test_assign_user_gift_cards_no_gift_cards_to_assign(
    customer_user, gift_card_created_by_staff
):
    # given
    gift_card_created_by_staff.created_by = None
    gift_card_created_by_staff.save(update_fields=["created_by"])

    # when
    assign_user_gift_cards(customer_user)

    # then
    gift_card_created_by_staff.refresh_from_db()
    assert not gift_card_created_by_staff.created_by


def test_is_gift_card_expired_never_expired_gift_card(gift_card):
    # given
    assert not gift_card.expiry_date

    # when
    result = is_gift_card_expired(gift_card)

    # then
    assert result is False


def test_is_gift_card_expired_true(gift_card):
    # given
    gift_card.expiry_date = date.today() - timedelta(days=1)
    gift_card.save(update_fields=["expiry_date"])

    # when
    result = is_gift_card_expired(gift_card)

    # then
    assert result is True


@pytest.mark.parametrize(
    "expiry_date", [timezone.now().date(), timezone.now().date() + timedelta(days=1)]
)
def test_is_gift_card_expired_false(expiry_date, gift_card):
    # given
    gift_card.expiry_date = expiry_date
    gift_card.save(update_fields=["expiry_date"])

    # when
    result = is_gift_card_expired(gift_card)

    # then
    assert result is False
