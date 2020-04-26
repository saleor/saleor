import datetime
from unittest.mock import Mock, patch

import pytest
import pytz
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from django_countries.fields import Country
from freezegun import freeze_time
from prices import Money, TaxedMoney

from saleor.account import CustomerEvents
from saleor.account.models import Address, CustomerEvent, User
from saleor.account.utils import store_user_address
from saleor.checkout import AddressType, calculations
from saleor.checkout.models import Checkout
from saleor.checkout.utils import (
    add_variant_to_checkout,
    add_voucher_to_checkout,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    clear_shipping_method,
    create_order,
    get_voucher_discount_for_checkout,
    get_voucher_for_checkout,
    is_valid_shipping_method,
    prepare_order_data,
    recalculate_checkout_discount,
    remove_voucher_from_checkout,
)
from saleor.core.exceptions import InsufficientStock
from saleor.core.taxes import zero_money, zero_taxed_money
from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.models import NotApplicable, Voucher
from saleor.order import OrderEvents, OrderEventsEmails
from saleor.order.models import OrderEvent
from saleor.plugins.manager import get_plugins_manager
from saleor.shipping.models import ShippingZone

from .utils import flush_post_commit_hooks


def test_is_valid_shipping_method(checkout_with_item, address, shipping_zone):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()
    lines = list(checkout)
    # no shipping method assigned
    assert not is_valid_shipping_method(checkout, lines, None)
    shipping_method = shipping_zone.shipping_methods.first()
    checkout.shipping_method = shipping_method
    checkout.save()

    assert is_valid_shipping_method(checkout, lines, None)

    zone = ShippingZone.objects.create(name="DE", countries=["DE"])
    shipping_method.shipping_zone = zone
    shipping_method.save()
    assert not is_valid_shipping_method(checkout, lines, None)


def test_clear_shipping_method(checkout, shipping_method):
    checkout.shipping_method = shipping_method
    checkout.save()
    clear_shipping_method(checkout)
    checkout.refresh_from_db()
    assert not checkout.shipping_method


def test_last_change_update(checkout):
    with freeze_time(datetime.datetime.now()) as frozen_datetime:
        assert checkout.last_change != frozen_datetime()

        checkout.note = "Sample note"
        checkout.save()

        assert checkout.last_change == pytz.utc.localize(frozen_datetime())


def test_last_change_update_foregin_key(checkout, shipping_method):
    with freeze_time(datetime.datetime.now()) as frozen_datetime:
        assert checkout.last_change != frozen_datetime()

        checkout.shipping_method = shipping_method
        checkout.save(update_fields=["shipping_method", "last_change"])

        assert checkout.last_change == pytz.utc.localize(frozen_datetime())


@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_creates_expected_events(
    request_checkout_with_item, customer_user, shipping_method, is_anonymous_user
):
    checkout = request_checkout_with_item
    checkout_user = None if is_anonymous_user else customer_user

    # Ensure not events are existing prior
    assert not OrderEvent.objects.exists()
    assert not CustomerEvent.objects.exists()

    # Prepare valid checkout
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_shipping_address
    checkout.shipping_method = shipping_method
    checkout.save()

    # Place checkout
    order = create_order(
        checkout=checkout,
        order_data=prepare_order_data(
            checkout=checkout,
            lines=list(checkout),
            tracking_code="tracking_code",
            discounts=None,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        redirect_url="https://www.example.com",
    )
    flush_post_commit_hooks()

    # Ensure only two events were created, and retrieve them
    placement_event, email_sent_event = order.events.all()  # type: OrderEvent

    # Ensure the correct order event was created
    assert placement_event.type == OrderEvents.PLACED  # is the event the expected type
    assert placement_event.user == checkout_user  # is the user anonymous/ the customer
    assert placement_event.order is order  # is the associated backref order valid
    assert placement_event.date  # ensure a date was set
    assert not placement_event.parameters  # should not have any additional parameters

    # Ensure the correct email sent event was created
    assert email_sent_event.type == OrderEvents.EMAIL_SENT  # should be email sent event
    assert email_sent_event.user == checkout_user  # ensure the user is none or valid
    assert email_sent_event.order is order  # ensure the mail event is related to order
    assert email_sent_event.date  # ensure a date was set
    assert email_sent_event.parameters == {  # ensure the correct parameters were set
        "email": order.get_customer_email(),
        "email_type": OrderEventsEmails.ORDER,
    }

    # Check no event was created if the user was anonymous
    if is_anonymous_user:
        assert not CustomerEvent.objects.exists()  # should not have created any event
        return  # we are done testing as the user is anonymous

    # Ensure the correct customer event was created if the user was not anonymous
    placement_event = customer_user.events.get()  # type: CustomerEvent
    assert placement_event.type == CustomerEvents.PLACED_ORDER  # check the event type
    assert placement_event.user == customer_user  # check the backref is valid
    assert placement_event.order == order  # check the associated order is valid
    assert placement_event.date  # ensure a date was set
    assert not placement_event.parameters  # should not have any additional parameters

    # mock_send_staff_order_confirmation.assert_called_once_with(order.pk)


def test_create_order_insufficient_stock(
    request_checkout, customer_user, product_without_shipping
):
    variant = product_without_shipping.variants.get()
    add_variant_to_checkout(request_checkout, variant, 10, check_quantity=False)
    request_checkout.user = customer_user
    request_checkout.billing_address = customer_user.default_billing_address
    request_checkout.shipping_address = customer_user.default_billing_address
    request_checkout.save()

    with pytest.raises(InsufficientStock):
        prepare_order_data(
            checkout=request_checkout,
            lines=list(request_checkout),
            tracking_code="tracking_code",
            discounts=None,
        )


def test_create_order_doesnt_duplicate_order(
    checkout_with_item, customer_user, shipping_method
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.save()

    order_data = prepare_order_data(
        checkout=checkout, lines=list(checkout), tracking_code="", discounts=None
    )

    order_1 = create_order(
        checkout=checkout,
        order_data=order_data,
        user=customer_user,
        redirect_url="https://www.example.com",
    )
    assert order_1.checkout_token == checkout.token

    order_2 = create_order(
        checkout=checkout,
        order_data=order_data,
        user=customer_user,
        redirect_url="https://www.example.com",
    )
    assert order_1.pk == order_2.pk


@pytest.mark.parametrize("is_anonymous_user", (True, False))
def test_create_order_with_gift_card(
    checkout_with_gift_card, customer_user, shipping_method, is_anonymous_user
):
    checkout_user = None if is_anonymous_user else customer_user
    checkout = checkout_with_gift_card
    checkout.user = checkout_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.save()

    lines = list(checkout)
    subtotal = calculations.checkout_subtotal(checkout=checkout, lines=lines)
    shipping_price = calculations.checkout_shipping_price(
        checkout=checkout, lines=lines
    )
    total_gross_without_gift_cards = (
        subtotal.gross + shipping_price.gross - checkout.discount
    )
    gift_cards_balance = checkout.get_total_gift_cards_balance()

    order = create_order(
        checkout=checkout,
        order_data=prepare_order_data(
            checkout=checkout,
            lines=lines,
            tracking_code="tracking_code",
            discounts=None,
        ),
        user=customer_user if not is_anonymous_user else AnonymousUser(),
        redirect_url="https://www.example.com",
    )

    assert order.gift_cards.count() == 1
    assert order.gift_cards.first().current_balance.amount == 0
    assert order.total.gross == (total_gross_without_gift_cards - gift_cards_balance)


def test_create_order_with_gift_card_partial_use(
    checkout_with_item, gift_card_used, customer_user, shipping_method
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.save()

    price_without_gift_card = calculations.checkout_total(
        checkout=checkout, lines=list(checkout)
    )
    gift_card_balance_before_order = gift_card_used.current_balance_amount

    checkout.gift_cards.add(gift_card_used)
    checkout.save()

    order = create_order(
        checkout=checkout,
        order_data=prepare_order_data(
            checkout=checkout,
            lines=list(checkout),
            tracking_code="tracking_code",
            discounts=None,
        ),
        user=customer_user,
        redirect_url="https://www.example.com",
    )

    gift_card_used.refresh_from_db()

    expected_old_balance = (
        price_without_gift_card.gross.amount + gift_card_used.current_balance_amount
    )

    assert order.gift_cards.count() > 0
    assert order.total == zero_taxed_money()
    assert gift_card_balance_before_order == expected_old_balance


def test_create_order_with_many_gift_cards(
    checkout_with_item,
    gift_card_created_by_staff,
    gift_card,
    customer_user,
    shipping_method,
):
    checkout = checkout_with_item
    checkout.user = customer_user
    checkout.billing_address = customer_user.default_billing_address
    checkout.shipping_address = customer_user.default_billing_address
    checkout.shipping_method = shipping_method
    checkout.save()

    price_without_gift_card = calculations.checkout_total(
        checkout=checkout, lines=list(checkout)
    )
    gift_cards_balance_before_order = (
        gift_card_created_by_staff.current_balance.amount
        + gift_card.current_balance.amount
    )

    checkout.gift_cards.add(gift_card_created_by_staff)
    checkout.gift_cards.add(gift_card)
    checkout.save()

    order = create_order(
        checkout=checkout,
        order_data=prepare_order_data(
            checkout=checkout,
            lines=list(checkout),
            tracking_code="tracking_code",
            discounts=None,
        ),
        user=customer_user,
        redirect_url="https://www.example.com",
    )

    gift_card_created_by_staff.refresh_from_db()
    gift_card.refresh_from_db()
    zero_price = zero_money()
    assert order.gift_cards.count() > 0
    assert gift_card_created_by_staff.current_balance == zero_price
    assert gift_card.current_balance == zero_price
    assert price_without_gift_card.gross.amount == (
        gift_cards_balance_before_order + order.total.gross.amount
    )


def test_note_in_created_order(request_checkout_with_item, address, customer_user):
    request_checkout_with_item.shipping_address = address
    request_checkout_with_item.note = "test_note"
    request_checkout_with_item.save()
    order = create_order(
        checkout=request_checkout_with_item,
        order_data=prepare_order_data(
            checkout=request_checkout_with_item,
            lines=list(request_checkout_with_item),
            tracking_code="tracking_code",
            discounts=None,
        ),
        user=customer_user,
        redirect_url="https://www.example.com",
    )
    assert order.customer_note == request_checkout_with_item.note


@pytest.mark.parametrize(
    "total, min_spent_amount, total_quantity, min_checkout_items_quantity, "
    "discount_value, discount_value_type, expected_value",
    [
        (20, 20, 2, 2, 50, DiscountValueType.PERCENTAGE, 10),
        (20, None, 2, None, 50, DiscountValueType.PERCENTAGE, 10),
        (20, 20, 2, 2, 5, DiscountValueType.FIXED, 5),
        (20, None, 2, None, 5, DiscountValueType.FIXED, 5),
    ],
)
def test_get_discount_for_checkout_value_voucher(
    total,
    min_spent_amount,
    total_quantity,
    min_checkout_items_quantity,
    discount_value,
    discount_value_type,
    expected_value,
    monkeypatch,
):
    voucher = Voucher(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        discount_value=discount_value,
        min_spent=(
            Money(min_spent_amount, "USD") if min_spent_amount is not None else None
        ),
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    checkout = Mock(spec=Checkout, quantity=total_quantity)
    subtotal = TaxedMoney(Money(total, "USD"), Money(total, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    discount = get_voucher_discount_for_checkout(voucher, checkout, [], [])
    assert discount == Money(expected_value, "USD")


@patch("saleor.discount.utils.validate_voucher")
def test_get_voucher_discount_for_checkout_voucher_validation(
    mock_validate_voucher, voucher, checkout_with_voucher
):
    get_voucher_discount_for_checkout(
        voucher, checkout_with_voucher, list(checkout_with_voucher)
    )
    manager = get_plugins_manager()
    subtotal = manager.calculate_checkout_subtotal(
        checkout_with_voucher, list(checkout_with_voucher), []
    )
    quantity = checkout_with_voucher.quantity
    customer_email = checkout_with_voucher.get_customer_email()
    mock_validate_voucher.assert_called_once_with(
        voucher, subtotal.gross, quantity, customer_email
    )


@pytest.mark.parametrize(
    "total, total_quantity, discount_value, discount_type, min_spent_amount, "
    "min_checkout_items_quantity",
    [
        ("99", 9, 10, DiscountValueType.FIXED, None, 10),
        ("99", 9, 10, DiscountValueType.FIXED, 100, None),
        ("99", 10, 10, DiscountValueType.PERCENTAGE, 100, 10),
        ("100", 9, 10, DiscountValueType.PERCENTAGE, 100, 10),
        ("99", 9, 10, DiscountValueType.PERCENTAGE, 100, 10),
    ],
)
def test_get_discount_for_checkout_entire_order_voucher_not_applicable(
    total,
    total_quantity,
    discount_value,
    discount_type,
    min_spent_amount,
    min_checkout_items_quantity,
    monkeypatch,
):
    voucher = Voucher(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_spent=(
            Money(min_spent_amount, "USD") if min_spent_amount is not None else None
        ),
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    checkout = Mock(spec=Checkout, quantity=total_quantity)
    subtotal = TaxedMoney(Money(total, "USD"), Money(total, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(voucher, checkout, [], [])


@pytest.mark.parametrize(
    "discount_value, discount_type, apply_once_per_order, discount_amount",
    [
        (5, DiscountValueType.FIXED, True, 5),
        (5, DiscountValueType.FIXED, False, 15),
        (10000, DiscountValueType.FIXED, True, 10),
        (10, DiscountValueType.PERCENTAGE, True, 1),
        (10, DiscountValueType.PERCENTAGE, False, 6),
    ],
)
def test_get_discount_for_checkout_specific_products_voucher(
    checkout_with_items,
    product_list,
    discount_value,
    discount_type,
    apply_once_per_order,
    discount_amount,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        discount_value=discount_value,
        apply_once_per_order=apply_once_per_order,
    )
    for product in product_list:
        voucher.products.add(product)
    discount = get_voucher_discount_for_checkout(
        voucher, checkout_with_items, list(checkout_with_items)
    )
    assert discount == Money(discount_amount, "USD")


@pytest.mark.parametrize(
    "total, total_quantity, discount_value, discount_type, min_spent_amount,"
    "min_checkout_items_quantity",
    [
        ("99", 9, 10, DiscountValueType.FIXED, None, 10),
        ("99", 9, 10, DiscountValueType.FIXED, 100, None),
        ("99", 10, 10, DiscountValueType.PERCENTAGE, 100, 10),
        ("100", 9, 10, DiscountValueType.PERCENTAGE, 100, 10),
        ("99", 9, 10, DiscountValueType.PERCENTAGE, 100, 10),
    ],
)
def test_get_discount_for_checkout_specific_products_voucher_not_applicable(
    monkeypatch,
    total,
    total_quantity,
    discount_value,
    discount_type,
    min_spent_amount,
    min_checkout_items_quantity,
):
    discounts = []
    monkeypatch.setattr(
        "saleor.checkout.utils.get_prices_of_discounted_specific_product",
        lambda checkout, discounts, product: [],
    )
    monkeypatch.setattr(
        "saleor.checkout.calculations.checkout_shipping_price",
        lambda _: TaxedMoney(Money(0, "USD"), Money(0, "USD")),
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: TaxedMoney(
            Money(total, "USD"), Money(total, "USD")
        ),
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: TaxedMoney(
            Money(total, "USD"), Money(total, "USD")
        ),
    )

    voucher = Voucher(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_spent=(
            Money(min_spent_amount, "USD") if min_spent_amount is not None else None
        ),
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    checkout = Mock(quantity=total_quantity, spec=Checkout)
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(voucher, checkout, [], discounts)


@pytest.mark.parametrize(
    "shipping_cost, shipping_country_code, discount_value, discount_type,"
    "countries, expected_value",
    [
        (10, None, 50, DiscountValueType.PERCENTAGE, [], 5),
        (10, None, 20, DiscountValueType.FIXED, [], 10),
        (10, "PL", 20, DiscountValueType.FIXED, [], 10),
        (5, "PL", 5, DiscountValueType.FIXED, ["PL"], 5),
    ],
)
def test_get_discount_for_checkout_shipping_voucher(
    shipping_cost,
    shipping_country_code,
    discount_value,
    discount_type,
    countries,
    expected_value,
    monkeypatch,
):
    subtotal = TaxedMoney(Money(100, "USD"), Money(100, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    shipping_total = Money(shipping_cost, "USD")
    checkout = Mock(
        spec=Checkout,
        is_shipping_required=Mock(return_value=True),
        shipping_method=Mock(get_total=Mock(return_value=shipping_total)),
        get_shipping_price=Mock(return_value=shipping_total),
        shipping_address=Mock(country=Country(shipping_country_code)),
    )
    voucher = Voucher(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        countries=countries,
    )
    discount = get_voucher_discount_for_checkout(voucher, checkout, [])
    assert discount == Money(expected_value, "USD")


def test_get_discount_for_checkout_shipping_voucher_all_countries(monkeypatch):
    subtotal = TaxedMoney(Money(100, "USD"), Money(100, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    shipping_total = TaxedMoney(Money(10, "USD"), Money(10, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_shipping_price",
        lambda checkout, lines, discounts: shipping_total,
    )
    checkout = Mock(
        spec=Checkout,
        is_shipping_required=Mock(return_value=True),
        shipping_method=Mock(get_total=Mock(return_value=shipping_total)),
        shipping_address=Mock(country=Country("PL")),
    )
    voucher = Voucher(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.PERCENTAGE,
        discount_value=50,
        countries=[],
    )

    discount = get_voucher_discount_for_checkout(voucher, checkout, [])

    assert discount == Money(5, "USD")


def test_get_discount_for_checkout_shipping_voucher_limited_countries(monkeypatch):
    subtotal = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    shipping_total = TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD"))
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    checkout = Mock(
        get_subtotal=Mock(return_value=subtotal),
        is_shipping_required=Mock(return_value=True),
        shipping_method=Mock(get_total=Mock(return_value=shipping_total)),
        shipping_address=Mock(country=Country("PL")),
    )
    voucher = Voucher(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.PERCENTAGE,
        discount_value=50,
        countries=["UK", "DE"],
    )

    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(voucher, checkout, [])


@pytest.mark.parametrize(
    "is_shipping_required, shipping_method, discount_value, discount_type,"
    "countries, min_spent_amount, min_checkout_items_quantity, subtotal,"
    "total_quantity, error_msg",
    [
        (
            True,
            Mock(shipping_zone=Mock(countries=["PL"])),
            10,
            DiscountValueType.FIXED,
            ["US"],
            None,
            None,
            TaxedMoney(Money(10, "USD"), Money(10, "USD")),
            10,
            "This offer is not valid in your country.",
        ),
        (
            True,
            None,
            10,
            DiscountValueType.FIXED,
            [],
            None,
            None,
            TaxedMoney(Money(10, "USD"), Money(10, "USD")),
            10,
            "Please select a shipping method first.",
        ),
        (
            False,
            None,
            10,
            DiscountValueType.FIXED,
            [],
            None,
            None,
            TaxedMoney(Money(10, "USD"), Money(10, "USD")),
            10,
            "Your order does not require shipping.",
        ),
        (
            True,
            Mock(price=Money(10, "USD")),
            10,
            DiscountValueType.FIXED,
            [],
            5,
            None,
            TaxedMoney(Money(2, "USD"), Money(2, "USD")),
            10,
            "This offer is only valid for orders over $5.00.",
        ),
        (
            True,
            Mock(price=Money(10, "USD")),
            10,
            DiscountValueType.FIXED,
            [],
            5,
            10,
            TaxedMoney(Money(5, "USD"), Money(5, "USD")),
            9,
            "This offer is only valid for orders with a minimum of 10 quantity.",
        ),
        (
            True,
            Mock(price=Money(10, "USD")),
            10,
            DiscountValueType.FIXED,
            [],
            5,
            10,
            TaxedMoney(Money(2, "USD"), Money(2, "USD")),
            9,
            "This offer is only valid for orders over $5.00.",
        ),
    ],
)
def test_get_discount_for_checkout_shipping_voucher_not_applicable(
    is_shipping_required,
    shipping_method,
    discount_value,
    discount_type,
    countries,
    min_spent_amount,
    min_checkout_items_quantity,
    subtotal,
    total_quantity,
    error_msg,
    monkeypatch,
):
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda checkout, lines, discounts: subtotal,
    )
    checkout = Mock(
        is_shipping_required=Mock(return_value=is_shipping_required),
        shipping_method=shipping_method,
        quantity=total_quantity,
        spec=Checkout,
    )

    voucher = Voucher(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_spent=(
            Money(min_spent_amount, "USD") if min_spent_amount is not None else None
        ),
        min_checkout_items_quantity=min_checkout_items_quantity,
        countries=countries,
    )
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(voucher, checkout, [])
    assert str(e.value) == error_msg


def test_get_voucher_for_checkout(checkout_with_voucher, voucher):
    checkout_voucher = get_voucher_for_checkout(checkout_with_voucher)
    assert checkout_voucher == voucher


def test_get_voucher_for_checkout_expired_voucher(checkout_with_voucher, voucher):
    date_yesterday = timezone.now() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()
    checkout_voucher = get_voucher_for_checkout(checkout_with_voucher)
    assert checkout_voucher is None


def test_get_voucher_for_checkout_no_voucher_code(checkout):
    checkout_voucher = get_voucher_for_checkout(checkout)
    assert checkout_voucher is None


def test_remove_voucher_from_checkout(checkout_with_voucher, voucher_translation_fr):
    checkout = checkout_with_voucher
    remove_voucher_from_checkout(checkout)

    assert not checkout.voucher_code
    assert not checkout.discount_name
    assert not checkout.translated_discount_name
    assert checkout.discount == zero_money()


def test_recalculate_checkout_discount(
    checkout_with_voucher, voucher, voucher_translation_fr, settings
):
    settings.LANGUAGE_CODE = "fr"
    voucher.discount_value = 10
    voucher.save()

    recalculate_checkout_discount(
        checkout_with_voucher, list(checkout_with_voucher), None
    )
    assert (
        checkout_with_voucher.translated_discount_name == voucher_translation_fr.name
    )  # noqa
    assert checkout_with_voucher.discount == Money("10.00", "USD")


def test_recalculate_checkout_discount_with_sale(
    checkout_with_voucher_percentage, discount_info
):
    checkout = checkout_with_voucher_percentage
    recalculate_checkout_discount(checkout, list(checkout), [discount_info])
    assert checkout.discount == Money("1.50", "USD")
    assert calculations.checkout_total(
        checkout=checkout, lines=list(checkout), discounts=[discount_info]
    ).gross == Money("13.50", "USD")


def test_recalculate_checkout_discount_voucher_not_applicable(
    checkout_with_voucher, voucher
):
    checkout = checkout_with_voucher
    voucher.min_spent = Money(100, "USD")
    voucher.save(update_fields=["min_spent_amount", "currency"])

    recalculate_checkout_discount(
        checkout_with_voucher, list(checkout_with_voucher), None
    )

    assert not checkout.voucher_code
    assert not checkout.discount_name
    assert checkout.discount == zero_money()


def test_recalculate_checkout_discount_expired_voucher(checkout_with_voucher, voucher):
    checkout = checkout_with_voucher
    date_yesterday = timezone.now() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()

    recalculate_checkout_discount(
        checkout_with_voucher, list(checkout_with_voucher), None
    )

    assert not checkout.voucher_code
    assert not checkout.discount_name
    assert checkout.discount == zero_money()


def test_recalculate_checkout_discount_free_shipping_subtotal_less_than_shipping(
    checkout_with_voucher_percentage_and_shipping,
    voucher_free_shipping,
    shipping_method,
):
    checkout = checkout_with_voucher_percentage_and_shipping

    lines = list(checkout)
    shipping_method.price = calculations.checkout_subtotal(
        checkout=checkout, lines=lines
    ).gross + Money("10.00", "USD")
    shipping_method.save()

    recalculate_checkout_discount(checkout, lines, None)

    assert checkout.discount == shipping_method.price
    assert checkout.discount_name == "Free shipping"
    assert calculations.checkout_total(
        checkout=checkout, lines=lines
    ) == calculations.checkout_subtotal(checkout=checkout, lines=lines)


def test_recalculate_checkout_discount_free_shipping_subtotal_bigger_than_shipping(
    checkout_with_voucher_percentage_and_shipping,
    voucher_free_shipping,
    shipping_method,
):
    checkout = checkout_with_voucher_percentage_and_shipping

    lines = list(checkout)
    shipping_method.price = calculations.checkout_subtotal(
        checkout=checkout, lines=lines
    ).gross - Money("1.00", "USD")
    shipping_method.save()

    recalculate_checkout_discount(checkout, lines, None)

    assert checkout.discount == shipping_method.price
    assert checkout.discount_name == "Free shipping"
    assert calculations.checkout_total(
        checkout=checkout, lines=lines
    ) == calculations.checkout_subtotal(checkout=checkout, lines=lines)


def test_recalculate_checkout_discount_free_shipping_for_checkout_without_shipping(
    checkout_with_voucher_percentage, voucher_free_shipping
):
    checkout = checkout_with_voucher_percentage

    recalculate_checkout_discount(checkout, list(checkout), None)

    assert not checkout.discount_name
    assert not checkout.voucher_code
    assert checkout.discount == zero_money()


def test_change_address_in_checkout(checkout, address):
    change_shipping_address_in_checkout(checkout, address)
    change_billing_address_in_checkout(checkout, address)

    checkout.refresh_from_db()
    assert checkout.shipping_address == address
    assert checkout.billing_address == address


def test_change_address_in_checkout_to_none(checkout, address):
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save()

    change_shipping_address_in_checkout(checkout, None)
    change_billing_address_in_checkout(checkout, None)

    checkout.refresh_from_db()
    assert checkout.shipping_address is None
    assert checkout.billing_address is None


def test_change_address_in_checkout_to_same(checkout, address):
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save(update_fields=["shipping_address", "billing_address"])
    shipping_address_id = checkout.shipping_address.id
    billing_address_id = checkout.billing_address.id

    change_shipping_address_in_checkout(checkout, address)
    change_billing_address_in_checkout(checkout, address)

    checkout.refresh_from_db()
    assert checkout.shipping_address.id == shipping_address_id
    assert checkout.billing_address.id == billing_address_id


def test_change_address_in_checkout_to_other(checkout, address):
    address_id = address.id
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save(update_fields=["shipping_address", "billing_address"])
    other_address = Address.objects.create(country=Country("DE"))

    change_shipping_address_in_checkout(checkout, other_address)
    change_billing_address_in_checkout(checkout, other_address)

    checkout.refresh_from_db()
    assert checkout.shipping_address == other_address
    assert checkout.billing_address == other_address
    assert not Address.objects.filter(id=address_id).exists()


def test_change_address_in_checkout_from_user_address_to_other(
    checkout, customer_user, address
):
    address_id = address.id
    checkout.user = customer_user
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save(update_fields=["shipping_address", "billing_address"])
    other_address = Address.objects.create(country=Country("DE"))

    change_shipping_address_in_checkout(checkout, other_address)
    change_billing_address_in_checkout(checkout, other_address)

    checkout.refresh_from_db()
    assert checkout.shipping_address == other_address
    assert checkout.billing_address == other_address
    assert Address.objects.filter(id=address_id).exists()


def test_add_voucher_to_checkout(checkout_with_item, voucher):
    assert checkout_with_item.voucher_code is None
    add_voucher_to_checkout(checkout_with_item, list(checkout_with_item), voucher)

    assert checkout_with_item.voucher_code == voucher.code


def test_add_voucher_to_checkout_fail(
    checkout_with_item, voucher_with_high_min_spent_amount
):
    with pytest.raises(NotApplicable):
        add_voucher_to_checkout(
            checkout_with_item,
            list(checkout_with_item),
            voucher_with_high_min_spent_amount,
        )

    assert checkout_with_item.voucher_code is None


def test_store_user_address_uses_existing_one(address):
    """Ensure storing an address that is already associated to the given user doesn't
    create a new address, but uses the existing one instead.
    """
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.add(address)

    expected_user_addresses_count = 1

    store_user_address(user, address, AddressType.BILLING)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id == address.pk


def test_store_user_address_uses_existing_one_despite_duplicated(address):
    """Ensure storing an address handles the possibility of an user
    having the same address associated to them multiple time is handled properly.

    It should use the first identical address associated to the user.
    """
    same_address = Address.objects.create(**address.as_data())
    user = User.objects.create_user("test@example.com", "password")
    user.addresses.set([address, same_address])

    expected_user_addresses_count = 2

    store_user_address(user, address, AddressType.BILLING)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id == address.pk


def test_store_user_address_create_new_address_if_not_associated(address):
    """Ensure storing an address that is not associated to the given user
    triggers the creation of a new address, but uses the existing one instead.
    """
    user = User.objects.create_user("test@example.com", "password")
    expected_user_addresses_count = 1

    store_user_address(user, address, AddressType.BILLING)

    assert user.addresses.count() == expected_user_addresses_count
    assert user.default_billing_address_id != address.pk
