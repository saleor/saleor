import datetime
from unittest.mock import Mock, patch

import pytest
import pytz
from django.utils import timezone
from django_countries.fields import Country
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ...account.models import Address, User
from ...account.utils import store_user_address
from ...core.taxes import zero_money
from ...discount import DiscountValueType, VoucherType
from ...discount.models import NotApplicable, Voucher, VoucherChannelListing
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...shipping.models import ShippingZone
from .. import AddressType, calculations
from ..models import Checkout
from ..utils import (
    add_voucher_to_checkout,
    cancel_active_payments,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    clear_shipping_method,
    fetch_checkout_lines,
    get_voucher_discount_for_checkout,
    get_voucher_for_checkout,
    is_fully_paid,
    is_valid_shipping_method,
    recalculate_checkout_discount,
    remove_voucher_from_checkout,
)


def test_is_valid_shipping_method(checkout_with_item, address, shipping_zone):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()
    lines = fetch_checkout_lines(checkout)
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
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_value_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
        min_spent_amount=(min_spent_amount if min_spent_amount is not None else None),
    )
    checkout = Mock(spec=Checkout, quantity=total_quantity, channel=channel_USD)
    subtotal = TaxedMoney(Money(total, "USD"), Money(total, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    manager = get_plugins_manager()
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout, [], None, []
    )
    assert discount == Money(expected_value, "USD")


@patch("saleor.discount.utils.validate_voucher")
def test_get_voucher_discount_for_checkout_voucher_validation(
    mock_validate_voucher, voucher, checkout_with_voucher
):
    lines = fetch_checkout_lines(checkout_with_voucher)
    manager = get_plugins_manager()
    address = checkout_with_voucher.shipping_address
    get_voucher_discount_for_checkout(
        manager, voucher, checkout_with_voucher, lines, address
    )
    subtotal = manager.calculate_checkout_subtotal(
        checkout_with_voucher, lines, address, []
    )
    quantity = checkout_with_voucher.quantity
    customer_email = checkout_with_voucher.get_customer_email()
    mock_validate_voucher.assert_called_once_with(
        voucher, subtotal.gross, quantity, customer_email, checkout_with_voucher.channel
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
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.ENTIRE_ORDER,
        discount_value_type=discount_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
        min_spent_amount=(min_spent_amount if min_spent_amount is not None else None),
    )
    checkout = Mock(spec=Checkout, quantity=total_quantity, channel=channel_USD)
    subtotal = TaxedMoney(Money(total, "USD"), Money(total, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    manager = get_plugins_manager()
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(manager, voucher, checkout, [], None, [])


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
    channel_USD,
):
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        apply_once_per_order=apply_once_per_order,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    for product in product_list:
        voucher.products.add(product)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_items)
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout_with_items, lines, None, []
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
    channel_USD,
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
        lambda manager, checkout, lines, address, discounts: TaxedMoney(
            Money(total, "USD"), Money(total, "USD")
        ),
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: TaxedMoney(
            Money(total, "USD"), Money(total, "USD")
        ),
    )

    manager = get_plugins_manager()
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
        min_spent_amount=(min_spent_amount if min_spent_amount is not None else None),
    )
    checkout = Mock(quantity=total_quantity, spec=Checkout, channel=channel_USD)
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(
            manager, voucher, checkout, [], None, discounts
        )


@pytest.mark.parametrize(
    "shipping_cost, shipping_country_code, discount_value, discount_type,"
    "countries, expected_value",
    [
        # (10, None, 50, DiscountValueType.PERCENTAGE, [], 5),
        # (10, None, 20, DiscountValueType.FIXED, [], 10),
        # (10, "PL", 20, DiscountValueType.FIXED, [], 10),
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
    channel_USD,
    shipping_method,
):
    manager = get_plugins_manager()
    subtotal = TaxedMoney(Money(100, "USD"), Money(100, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.is_shipping_required", lambda lines: True
    )
    shipping_total = Money(shipping_cost, "USD")
    checkout = Mock(
        spec=Checkout,
        is_shipping_required=Mock(return_value=True),
        channel_id=channel_USD.id,
        channel=channel_USD,
        shipping_method=shipping_method,
        get_shipping_price=Mock(return_value=shipping_total),
        shipping_address=Mock(country=Country(shipping_country_code)),
    )
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        countries=countries,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout, [], None, None
    )
    assert discount == Money(expected_value, "USD")


def test_get_discount_for_checkout_shipping_voucher_all_countries(
    monkeypatch, channel_USD, shipping_method
):
    subtotal = TaxedMoney(Money(100, "USD"), Money(100, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.is_shipping_required", lambda lines: True
    )
    shipping_total = TaxedMoney(Money(10, "USD"), Money(10, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_shipping_price",
        lambda manager, checkout, lines, address, discounts: shipping_total,
    )
    checkout = Mock(
        spec=Checkout,
        channel_id=channel_USD.id,
        channel=channel_USD,
        shipping_method_id=shipping_method.id,
        is_shipping_required=Mock(return_value=True),
        shipping_method=Mock(get_total=Mock(return_value=shipping_total)),
        shipping_address=Mock(country=Country("PL")),
    )
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.PERCENTAGE,
        countries=[],
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )

    manager = get_plugins_manager()
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout, [], None, None
    )

    assert discount == Money(5, "USD")


def test_get_discount_for_checkout_shipping_voucher_limited_countries(
    monkeypatch, channel_USD
):
    subtotal = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    shipping_total = TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD"))
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    checkout = Mock(
        get_subtotal=Mock(return_value=subtotal),
        channel=channel_USD,
        is_shipping_required=Mock(return_value=True),
        shipping_method=Mock(get_total=Mock(return_value=shipping_total)),
        shipping_address=Mock(country=Country("PL")),
    )
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.PERCENTAGE,
        countries=["UK", "DE"],
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(50, channel_USD.currency_code),
    )

    manager = get_plugins_manager()
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(manager, voucher, checkout, [], None, [])


@pytest.mark.parametrize(
    "is_shipping_required, shipping_method, discount_value, discount_type,"
    "countries, min_spent_amount, min_checkout_items_quantity, subtotal,"
    "total_quantity, error_msg",
    [
        (
            True,
            Mock(
                get_total=Mock(return_value=Money(10, "USD")),
                shipping_zone=Mock(countries=["PL"]),
            ),
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
    channel_USD,
):
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.is_shipping_required", lambda lines: is_shipping_required
    )
    checkout = Mock(
        is_shipping_required=Mock(return_value=is_shipping_required),
        shipping_method=shipping_method,
        shipping_address=Mock(spec=Address, country=Mock(code="PL")),
        quantity=total_quantity,
        spec=Checkout,
        channel=channel_USD,
    )

    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        min_checkout_items_quantity=min_checkout_items_quantity,
        countries=countries,
    )
    manager = get_plugins_manager()
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
        min_spent_amount=(min_spent_amount if min_spent_amount is not None else None),
    )
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(
            manager, voucher, checkout, [], checkout.shipping_address, None
        )
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
    assert checkout.discount == zero_money(checkout.channel.currency_code)


def test_recalculate_checkout_discount(
    checkout_with_voucher, voucher, voucher_translation_fr, settings, channel_USD
):
    settings.LANGUAGE_CODE = "fr"
    voucher.channel_listings.filter(channel=channel_USD).update(discount_value=10)

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_voucher)

    recalculate_checkout_discount(manager, checkout_with_voucher, lines, None)
    assert (
        checkout_with_voucher.translated_discount_name == voucher_translation_fr.name
    )  # noqa
    assert checkout_with_voucher.discount == Money("10.00", "USD")


def test_recalculate_checkout_discount_with_sale(
    checkout_with_voucher_percentage, discount_info
):
    checkout = checkout_with_voucher_percentage
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    recalculate_checkout_discount(manager, checkout, lines, [discount_info])
    assert checkout.discount == Money("1.50", "USD")
    assert (
        calculations.checkout_total(
            manager=manager,
            checkout=checkout,
            lines=lines,
            address=checkout.shipping_address,
            discounts=[discount_info],
        ).gross
        == Money("13.50", "USD")
    )


def test_recalculate_checkout_discount_voucher_not_applicable(
    checkout_with_voucher, voucher, channel_USD
):
    checkout = checkout_with_voucher
    voucher.channel_listings.filter(channel=channel_USD).update(min_spent_amount=100)

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    recalculate_checkout_discount(manager, checkout, lines, None)

    assert not checkout.voucher_code
    assert not checkout.discount_name
    assert checkout.discount == zero_money(checkout.channel.currency_code)


def test_recalculate_checkout_discount_expired_voucher(checkout_with_voucher, voucher):
    checkout = checkout_with_voucher
    date_yesterday = timezone.now() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    recalculate_checkout_discount(manager, checkout, lines, None)

    assert not checkout.voucher_code
    assert not checkout.discount_name
    assert checkout.discount == zero_money(checkout.channel.currency_code)


def test_recalculate_checkout_discount_free_shipping_subtotal_less_than_shipping(
    checkout_with_voucher_percentage_and_shipping,
    voucher_free_shipping,
    shipping_method,
    channel_USD,
):
    checkout = checkout_with_voucher_percentage_and_shipping
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    channel_listing = shipping_method.channel_listings.get(channel_id=channel_USD.id)
    channel_listing.price = (
        calculations.checkout_subtotal(
            manager=manager,
            checkout=checkout,
            lines=lines,
            address=checkout.shipping_address,
        ).gross
        + Money("10.00", "USD")
    )
    channel_listing.save()

    recalculate_checkout_discount(manager, checkout, lines, None)

    assert checkout.discount == channel_listing.price
    assert checkout.discount_name == "Free shipping"
    checkout_total = calculations.checkout_total(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert checkout_total == checkout_subtotal


def test_recalculate_checkout_discount_free_shipping_subtotal_bigger_than_shipping(
    checkout_with_voucher_percentage_and_shipping,
    voucher_free_shipping,
    shipping_method,
    channel_USD,
):
    checkout = checkout_with_voucher_percentage_and_shipping
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    channel_listing = shipping_method.channel_listings.get(channel=channel_USD)
    channel_listing.price = (
        calculations.checkout_subtotal(
            manager=manager,
            checkout=checkout,
            lines=lines,
            address=checkout.shipping_address,
        ).gross
        - Money("1.00", "USD")
    )
    channel_listing.save()

    recalculate_checkout_discount(manager, checkout, lines, None)

    assert checkout.discount == channel_listing.price
    assert checkout.discount_name == "Free shipping"
    checkout_total = calculations.checkout_total(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert checkout_total == checkout_subtotal


def test_recalculate_checkout_discount_free_shipping_for_checkout_without_shipping(
    checkout_with_voucher_percentage, voucher_free_shipping
):
    checkout = checkout_with_voucher_percentage
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    recalculate_checkout_discount(manager, checkout, lines, None)

    assert not checkout.discount_name
    assert not checkout.voucher_code
    assert checkout.discount == zero_money(checkout.channel.currency_code)


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
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    add_voucher_to_checkout(manager, checkout_with_item, lines, voucher)
    assert checkout_with_item.voucher_code == voucher.code


def test_add_voucher_to_checkout_fail(
    checkout_with_item, voucher_with_high_min_spent_amount
):
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout_with_item)
    with pytest.raises(NotApplicable):
        add_voucher_to_checkout(
            manager,
            checkout_with_item,
            lines,
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


def test_get_last_active_payment(checkout_with_payments):
    # given
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        checkout=checkout_with_payments,
    )

    # when
    last_payment = checkout_with_payments.get_last_active_payment()

    # then
    assert last_payment.pk == payment.pk


def test_is_fully_paid(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    is_paid = is_fully_paid(manager, checkout, lines, None)
    assert is_paid


def test_is_fully_paid_many_payments(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount - 1
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    payment2 = payment_dummy
    payment2.pk = None
    payment2.is_active = True
    payment2.order = None
    payment2.total = 1
    payment2.currency = total.gross.currency
    payment2.checkout = checkout
    payment2.save()
    is_paid = is_fully_paid(manager, checkout, lines, None)
    assert is_paid


def test_is_fully_paid_partially_paid(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager,
        checkout=checkout,
        lines=lines,
        address=checkout.shipping_address,
    )
    payment = payment_dummy
    payment.is_active = True
    payment.order = None
    payment.total = total.gross.amount - 1
    payment.currency = total.gross.currency
    payment.checkout = checkout
    payment.save()
    is_paid = is_fully_paid(manager, checkout, lines, None)
    assert not is_paid


def test_is_fully_paid_no_payment(checkout_with_item):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    is_paid = is_fully_paid(manager, checkout, lines, None)
    assert not is_paid


def test_cancel_active_payments(checkout_with_payments):
    # given
    checkout = checkout_with_payments
    count_active = checkout.payments.filter(is_active=True).count()
    assert count_active != 0

    # when
    cancel_active_payments(checkout)

    # then
    assert checkout.payments.filter(is_active=True).count() == 0
