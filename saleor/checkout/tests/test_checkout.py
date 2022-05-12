import datetime
from unittest.mock import Mock, patch

import graphene
import pytest
import pytz
from django.utils import timezone
from django_countries.fields import Country
from freezegun import freeze_time
from prices import Money, TaxedMoney

from ...account.models import Address
from ...core.taxes import zero_money
from ...discount import DiscountValueType, VoucherType
from ...discount.models import NotApplicable, Voucher, VoucherChannelListing
from ...payment.models import Payment
from ...plugins.manager import get_plugins_manager
from ...shipping.interface import ShippingMethodData
from ...shipping.models import ShippingZone
from .. import calculations
from ..fetch import (
    CheckoutInfo,
    CheckoutLineInfo,
    DeliveryMethodBase,
    fetch_checkout_info,
    fetch_checkout_lines,
    get_delivery_method_info,
)
from ..models import Checkout
from ..utils import (
    PRIVATE_META_APP_SHIPPING_ID,
    add_voucher_to_checkout,
    calculate_checkout_quantity,
    cancel_active_payments,
    change_billing_address_in_checkout,
    change_shipping_address_in_checkout,
    clear_delivery_method,
    delete_external_shipping_id,
    get_external_shipping_id,
    get_voucher_discount_for_checkout,
    get_voucher_for_checkout_info,
    is_fully_paid,
    recalculate_checkout_discount,
    remove_voucher_from_checkout,
    set_external_shipping_id,
)


def test_is_valid_delivery_method(checkout_with_item, address, shipping_zone):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method_info = checkout_info.delivery_method_info
    # no shipping method assigned
    assert not delivery_method_info.is_valid_delivery_method()
    shipping_method = shipping_zone.shipping_methods.first()
    checkout.shipping_method = shipping_method
    checkout.save()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method_info = checkout_info.delivery_method_info

    assert delivery_method_info.is_valid_delivery_method()

    zone = ShippingZone.objects.create(name="DE", countries=["DE"])
    shipping_method.shipping_zone = zone
    shipping_method.save()
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method_info = checkout_info.delivery_method_info

    assert not delivery_method_info.is_method_in_valid_methods(checkout_info)


@patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_is_valid_delivery_method_external_method(
    mock_send_request, checkout_with_item, address, settings, shipping_app
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    response_method_id = "abcd"
    mock_json_response = [
        {
            "id": response_method_id,
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{response_method_id}"
    )

    mock_send_request.return_value = mock_json_response
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.private_metadata = {PRIVATE_META_APP_SHIPPING_ID: method_id}
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method_info = checkout_info.delivery_method_info

    assert delivery_method_info.is_method_in_valid_methods(checkout_info)


@patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_is_valid_delivery_method_external_method_no_longer_available(
    mock_send_request, checkout_with_item, address, settings, shipping_app
):
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    mock_json_response = [
        {
            "id": "New-ID",
            "name": "Provider - Economy",
            "amount": "10",
            "currency": "USD",
            "maximum_delivery_days": "7",
        }
    ]
    method_id = graphene.Node.to_global_id("app", f"{shipping_app.id}:1")

    mock_send_request.return_value = mock_json_response
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.private_metadata = {PRIVATE_META_APP_SHIPPING_ID: method_id}
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method_info = checkout_info.delivery_method_info

    assert delivery_method_info.is_method_in_valid_methods(checkout_info) is False


def test_clear_delivery_method(checkout, shipping_method):
    checkout.shipping_method = shipping_method
    checkout.save()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    clear_delivery_method(checkout_info)
    checkout.refresh_from_db()
    assert not checkout.shipping_method
    assert isinstance(checkout_info.delivery_method_info, DeliveryMethodBase)


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
    "total, min_spent_amount, min_checkout_items_quantity, "
    "discount_value, discount_value_type, expected_value",
    [
        (20, 20, 2, 50, DiscountValueType.PERCENTAGE, 10),
        (20, None, None, 50, DiscountValueType.PERCENTAGE, 10),
        (20, 20, 2, 5, DiscountValueType.FIXED, 5),
        (20, None, None, 5, DiscountValueType.FIXED, 5),
    ],
)
def test_get_discount_for_checkout_value_voucher(
    total,
    min_spent_amount,
    min_checkout_items_quantity,
    discount_value,
    discount_value_type,
    expected_value,
    monkeypatch,
    channel_USD,
    checkout_with_items,
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
    checkout = Mock(spec=checkout_with_items, channel=channel_USD)
    subtotal = TaxedMoney(Money(total, "USD"), Money(total, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    checkout_info = CheckoutInfo(
        checkout=checkout,
        shipping_address=None,
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        delivery_method_info=get_delivery_method_info(None, None),
        all_shipping_methods=[],
    )
    lines = [
        CheckoutLineInfo(
            line=line,
            channel_listing=line.variant.product.channel_listings.first(),
            collections=[],
            product=line.variant.product,
            variant=line.variant,
            product_type=line.variant.product.product_type,
        )
        for line in checkout_with_items.lines.all()
    ]
    manager = get_plugins_manager()
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout_info, lines, None, []
    )
    assert discount == Money(expected_value, "USD")


@patch("saleor.discount.utils.validate_voucher")
def test_get_voucher_discount_for_checkout_voucher_validation(
    mock_validate_voucher, voucher, checkout_with_voucher
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_voucher)
    quantity = calculate_checkout_quantity(lines)
    checkout_info = fetch_checkout_info(checkout_with_voucher, lines, [], manager)
    manager = get_plugins_manager()
    address = checkout_with_voucher.shipping_address
    get_voucher_discount_for_checkout(manager, voucher, checkout_info, lines, address)
    subtotal = manager.calculate_checkout_subtotal(checkout_info, lines, address, [])
    customer_email = checkout_with_voucher.get_customer_email()
    mock_validate_voucher.assert_called_once_with(
        voucher,
        subtotal,
        quantity,
        customer_email,
        checkout_with_voucher.channel,
        checkout_info.user,
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
    checkout = Mock(spec=Checkout, channel=channel_USD)
    subtotal = TaxedMoney(Money(total, "USD"), Money(total, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    checkout_info = CheckoutInfo(
        checkout=checkout,
        delivery_method_info=None,
        shipping_address=None,
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        all_shipping_methods=[],
    )
    manager = get_plugins_manager()
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(manager, voucher, checkout_info, [], None, [])


@pytest.mark.parametrize(
    "discount_value, discount_type, total_discount_amount",
    [
        (5, DiscountValueType.FIXED, 15),
        (10, DiscountValueType.PERCENTAGE, 6),
    ],
)
def test_get_discount_for_checkout_specific_products_voucher(
    checkout_with_items,
    product_list,
    discount_value,
    discount_type,
    total_discount_amount,
    channel_USD,
):
    # given
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        apply_once_per_order=False,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    for product in product_list:
        voucher.products.add(product)
    checkout_with_items.voucher_code = voucher.code
    checkout_with_items.save()
    manager = get_plugins_manager()

    # when
    lines, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, [], manager)
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, []
    ).gross

    # then
    for line in lines:
        line.voucher = None
    subtotal_without_voucher = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, []
    )

    currency = checkout_info.checkout.currency
    expected_subtotal = subtotal_without_voucher.gross - Money(
        total_discount_amount, currency
    )
    assert expected_subtotal == subtotal


@pytest.mark.parametrize(
    "discount_value, discount_type, total_discount_amount",
    [
        (5, DiscountValueType.FIXED, 5),
        (10000, DiscountValueType.FIXED, 10),
        (10, DiscountValueType.PERCENTAGE, 1),
    ],
)
def test_get_discount_for_checkout_specific_products_voucher_apply_only_once(
    checkout_with_items,
    product_list,
    discount_value,
    discount_type,
    total_discount_amount,
    channel_USD,
):
    # given
    voucher = Voucher.objects.create(
        code="unique",
        type=VoucherType.SPECIFIC_PRODUCT,
        discount_value_type=discount_type,
        apply_once_per_order=True,
    )
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(discount_value, channel_USD.currency_code),
    )
    for product in product_list:
        voucher.products.add(product)
    checkout_with_items.voucher_code = voucher.code
    checkout_with_items.save()
    manager = get_plugins_manager()

    # when
    lines, _ = fetch_checkout_lines(checkout_with_items)
    checkout_info = fetch_checkout_info(checkout_with_items, lines, [], manager)
    subtotal = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, []
    ).gross

    # then
    assert any([line.voucher is not None for line in lines])
    for line in lines:
        line.voucher = None
    subtotal_without_voucher = manager.calculate_checkout_subtotal(
        checkout_info, lines, checkout_info.shipping_address, []
    )

    assert subtotal == subtotal_without_voucher.gross - Money(
        total_discount_amount, checkout_info.checkout.currency
    )


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
        lambda manager, checkout_info, lines, address, discounts: TaxedMoney(
            Money(total, "USD"), Money(total, "USD")
        ),
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: TaxedMoney(
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
    checkout_info = CheckoutInfo(
        checkout=checkout,
        delivery_method_info=get_delivery_method_info(None, None),
        shipping_address=None,
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        all_shipping_methods=[],
    )
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(
            manager, voucher, checkout_info, [], None, discounts
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
    shipping_method_data,
):
    manager = get_plugins_manager()
    subtotal = TaxedMoney(Money(100, "USD"), Money(100, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
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
    shipping_address = Mock(spec=Address, country=Mock(code="PL"))
    checkout_info = CheckoutInfo(
        checkout=checkout,
        shipping_address=shipping_address,
        delivery_method_info=get_delivery_method_info(
            shipping_method_data, shipping_address
        ),
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        all_shipping_methods=[],
    )

    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout_info, [], None, None
    )
    assert discount == Money(expected_value, "USD")


def test_get_discount_for_checkout_shipping_voucher_all_countries(
    monkeypatch, channel_USD, shipping_method, shipping_method_data
):
    subtotal = TaxedMoney(Money(100, "USD"), Money(100, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.checkout.utils.is_shipping_required", lambda lines: True
    )
    shipping_total = TaxedMoney(Money(10, "USD"), Money(10, "USD"))
    monkeypatch.setattr(
        "saleor.checkout.utils.calculations.checkout_shipping_price",
        lambda manager, checkout_info, lines, address, discounts: shipping_total,
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
    checkout_info = CheckoutInfo(
        checkout=checkout,
        delivery_method_info=get_delivery_method_info(shipping_method_data),
        shipping_address=Mock(spec=Address, country=Mock(code="PL")),
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        all_shipping_methods=[],
    )
    discount = get_voucher_discount_for_checkout(
        manager, voucher, checkout_info, [], None, None
    )

    assert discount == Money(5, "USD")


def test_get_discount_for_checkout_shipping_voucher_limited_countries(
    monkeypatch, channel_USD
):
    subtotal = TaxedMoney(net=Money(100, "USD"), gross=Money(100, "USD"))
    shipping_total = TaxedMoney(net=Money(10, "USD"), gross=Money(10, "USD"))
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
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

    checkout_info = CheckoutInfo(
        checkout=checkout,
        delivery_method_info=get_delivery_method_info(None, None),
        shipping_address=Mock(spec=Address, country=Mock(code="PL")),
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        all_shipping_methods=[],
    )
    manager = get_plugins_manager()
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_checkout(manager, voucher, checkout_info, [], None, [])


@pytest.mark.parametrize(
    "is_shipping_required, shipping_method_data, discount_value, discount_type,"
    "countries, min_spent_amount, min_checkout_items_quantity, subtotal,"
    "total_quantity, error_msg",
    [
        (
            True,
            ShippingMethodData("1", "test", Money(10, "USD")),
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
            "Please select a delivery method first.",
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
            ShippingMethodData("1", "test", Money(10, "USD")),
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
            ShippingMethodData("1", "test", Money(10, "USD")),
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
            ShippingMethodData("1", "test", Money(10, "USD")),
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
    shipping_method_data,
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
        lambda manager, checkout_info, lines, address, discounts: subtotal,
    )
    monkeypatch.setattr(
        "saleor.discount.utils.calculations.checkout_subtotal",
        lambda manager, checkout_info, lines, address, discounts: subtotal,
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
    checkout_info = CheckoutInfo(
        checkout=checkout,
        delivery_method_info=get_delivery_method_info(shipping_method_data),
        shipping_address=Mock(spec=Address, country=Mock(code="PL")),
        billing_address=None,
        channel=channel_USD,
        user=None,
        valid_pick_up_points=[],
        all_shipping_methods=[],
    )
    with pytest.raises(NotApplicable) as e:
        get_voucher_discount_for_checkout(
            manager, voucher, checkout_info, [], checkout.shipping_address, None
        )
    assert str(e.value) == error_msg


def test_get_voucher_for_checkout_info(checkout_with_voucher, voucher):
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout_with_voucher, [], [], manager)
    checkout_voucher = get_voucher_for_checkout_info(checkout_info)
    assert checkout_voucher == voucher


def test_get_voucher_for_checkout_info_expired_voucher(checkout_with_voucher, voucher):
    date_yesterday = timezone.now() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout_with_voucher, [], [], manager)
    checkout_voucher = get_voucher_for_checkout_info(checkout_info)
    assert checkout_voucher is None


def test_get_voucher_for_checkout_info_no_voucher_code(checkout):
    manager = get_plugins_manager()
    checkout_info = fetch_checkout_info(checkout, [], [], manager)
    checkout_voucher = get_voucher_for_checkout_info(checkout_info)
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
    lines, _ = fetch_checkout_lines(checkout_with_voucher)
    checkout_info = fetch_checkout_info(checkout_with_voucher, lines, [], manager)

    recalculate_checkout_discount(manager, checkout_info, lines, None)
    assert (
        checkout_with_voucher.translated_discount_name == voucher_translation_fr.name
    )  # noqa
    assert checkout_with_voucher.discount == Money("10.00", "USD")


def test_recalculate_checkout_discount_with_sale(
    checkout_with_voucher_percentage, discount_info
):
    checkout = checkout_with_voucher_percentage
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)

    recalculate_checkout_discount(manager, checkout_info, lines, [discount_info])
    assert checkout.discount == Money("1.50", "USD")
    assert calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
        discounts=[discount_info],
    ).gross == Money("13.50", "USD")


def test_recalculate_checkout_discount_voucher_not_applicable(
    checkout_with_voucher, voucher, channel_USD
):
    checkout = checkout_with_voucher
    voucher.channel_listings.filter(channel=channel_USD).update(min_spent_amount=100)

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    recalculate_checkout_discount(manager, checkout_info, lines, None)

    assert not checkout.voucher_code
    assert not checkout.discount_name
    assert checkout.discount == zero_money(checkout.channel.currency_code)


def test_recalculate_checkout_discount_expired_voucher(checkout_with_voucher, voucher):
    checkout = checkout_with_voucher
    date_yesterday = timezone.now() - datetime.timedelta(days=1)
    voucher.end_date = date_yesterday
    voucher.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    recalculate_checkout_discount(manager, checkout_info, lines, None)

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
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    channel_listing = shipping_method.channel_listings.get(channel_id=channel_USD.id)
    channel_listing.price = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    ).gross + Money("10.00", "USD")
    channel_listing.save()

    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    recalculate_checkout_discount(manager, checkout_info, lines, None)

    assert checkout.discount == channel_listing.price
    assert checkout.discount_name == "Free shipping"
    checkout_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
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
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    channel_listing = shipping_method.channel_listings.get(channel=channel_USD)
    channel_listing.price = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    ).gross - Money("1.00", "USD")
    channel_listing.save()

    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    recalculate_checkout_discount(manager, checkout_info, lines, None)

    assert checkout.discount == channel_listing.price
    assert checkout.discount_name == "Free shipping"
    checkout_total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    checkout_subtotal = calculations.checkout_subtotal(
        manager=manager,
        checkout_info=checkout_info,
        lines=lines,
        address=checkout.shipping_address,
    )
    assert checkout_total == checkout_subtotal


def test_recalculate_checkout_discount_free_shipping_for_checkout_without_shipping(
    checkout_with_voucher_percentage, voucher_free_shipping
):
    checkout = checkout_with_voucher_percentage
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    recalculate_checkout_discount(manager, checkout_info, lines, None)

    assert not checkout.discount_name
    assert not checkout.voucher_code
    assert checkout.discount == zero_money(checkout.channel.currency_code)


def test_change_address_in_checkout(checkout, address):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    change_shipping_address_in_checkout(
        checkout_info,
        address,
        lines,
        [],
        manager,
        checkout.channel.shipping_method_listings.all(),
    )
    change_billing_address_in_checkout(checkout, address)

    checkout.refresh_from_db()
    assert checkout.shipping_address == address
    assert checkout.billing_address == address
    assert checkout_info.shipping_address == address


def test_change_address_in_checkout_to_none(checkout, address):
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save()

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    change_shipping_address_in_checkout(
        checkout_info,
        None,
        lines,
        [],
        manager,
        checkout.channel.shipping_method_listings.all(),
    )
    change_billing_address_in_checkout(checkout, None)

    checkout.refresh_from_db()
    assert checkout.shipping_address is None
    assert checkout.billing_address is None
    assert checkout_info.shipping_address is None


def test_change_address_in_checkout_to_same(checkout, address):
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save(update_fields=["shipping_address", "billing_address"])
    shipping_address_id = checkout.shipping_address.id
    billing_address_id = checkout.billing_address.id

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    change_shipping_address_in_checkout(
        checkout_info,
        address,
        lines,
        [],
        manager,
        checkout.channel.shipping_method_listings.all(),
    )
    change_billing_address_in_checkout(checkout, address)

    checkout.refresh_from_db()
    assert checkout.shipping_address.id == shipping_address_id
    assert checkout.billing_address.id == billing_address_id
    assert checkout_info.shipping_address == address


def test_change_address_in_checkout_to_other(checkout, address):
    address_id = address.id
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save(update_fields=["shipping_address", "billing_address"])
    other_address = Address.objects.create(country=Country("DE"))

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    change_shipping_address_in_checkout(
        checkout_info,
        other_address,
        lines,
        [],
        manager,
        checkout.channel.shipping_method_listings.all(),
    )
    change_billing_address_in_checkout(checkout, other_address)

    checkout.refresh_from_db()
    assert checkout.shipping_address == other_address
    assert checkout.billing_address == other_address
    assert not Address.objects.filter(id=address_id).exists()
    assert checkout_info.shipping_address == other_address


def test_change_address_in_checkout_from_user_address_to_other(
    checkout, customer_user, address
):
    address_id = address.id
    checkout.user = customer_user
    checkout.shipping_address = address
    checkout.billing_address = address.get_copy()
    checkout.save(update_fields=["shipping_address", "billing_address"])
    other_address = Address.objects.create(country=Country("DE"))

    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    change_shipping_address_in_checkout(
        checkout_info,
        other_address,
        lines,
        [],
        manager,
        checkout.channel.shipping_method_listings.all(),
    )
    change_billing_address_in_checkout(checkout, other_address)

    checkout.refresh_from_db()
    assert checkout.shipping_address == other_address
    assert checkout.billing_address == other_address
    assert Address.objects.filter(id=address_id).exists()
    assert checkout_info.shipping_address == other_address


def test_add_voucher_to_checkout(checkout_with_item, voucher):
    assert checkout_with_item.voucher_code is None
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    add_voucher_to_checkout(manager, checkout_info, lines, voucher)
    assert checkout_with_item.voucher_code == voucher.code


def test_add_staff_voucher_to_anonymous_checkout(checkout_with_item, voucher):
    voucher.only_for_staff = True
    voucher.save()

    assert checkout_with_item.voucher_code is None
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    with pytest.raises(NotApplicable):
        add_voucher_to_checkout(manager, checkout_info, lines, voucher)


def test_add_staff_voucher_to_customer_checkout(
    checkout_with_item, voucher, customer_user
):
    checkout_with_item.user = customer_user
    checkout_with_item.save()
    voucher.only_for_staff = True
    voucher.save()

    assert checkout_with_item.voucher_code is None
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    with pytest.raises(NotApplicable):
        add_voucher_to_checkout(manager, checkout_info, lines, voucher)


def test_add_staff_voucher_to_staff_checkout(checkout_with_item, voucher, staff_user):
    checkout_with_item.user = staff_user
    checkout_with_item.save()
    voucher.only_for_staff = True
    voucher.save()

    assert checkout_with_item.voucher_code is None
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)

    add_voucher_to_checkout(manager, checkout_info, lines, voucher)


def test_add_voucher_to_checkout_fail(
    checkout_with_item, voucher_with_high_min_spent_amount
):
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout_with_item)
    checkout_info = fetch_checkout_info(checkout_with_item, lines, [], manager)
    with pytest.raises(NotApplicable):
        add_voucher_to_checkout(
            manager,
            checkout_info,
            lines,
            voucher_with_high_min_spent_amount,
        )

    assert checkout_with_item.voucher_code is None


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
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
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
    is_paid = is_fully_paid(manager, checkout_info, lines, None)
    assert is_paid


def test_is_fully_paid_many_payments(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
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
    is_paid = is_fully_paid(manager, checkout_info, lines, None)
    assert is_paid


def test_is_fully_paid_partially_paid(checkout_with_item, payment_dummy):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    total = calculations.checkout_total(
        manager=manager,
        checkout_info=checkout_info,
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
    is_paid = is_fully_paid(manager, checkout_info, lines, None)
    assert not is_paid


def test_is_fully_paid_no_payment(checkout_with_item):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    is_paid = is_fully_paid(manager, checkout_info, lines, None)
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


def test_chckout_without_delivery_method_creates_empty_delivery_method(
    checkout_with_item,
):
    checkout = checkout_with_item
    manager = get_plugins_manager()
    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, [], manager)
    delivery_method_info = checkout_info.delivery_method_info

    assert isinstance(delivery_method_info, DeliveryMethodBase)
    assert not delivery_method_info.is_valid_delivery_method()
    assert not delivery_method_info.is_local_collection_point
    assert not delivery_method_info.is_method_in_valid_methods(checkout_info)


def test_manage_external_shipping_id(checkout):
    app_shipping_id = "abcd"
    initial_private_metadata = {"test": 123}
    checkout.private_metadata = initial_private_metadata

    set_external_shipping_id(checkout, app_shipping_id)
    assert PRIVATE_META_APP_SHIPPING_ID in checkout.private_metadata

    shipping_id = get_external_shipping_id(checkout)
    assert shipping_id == app_shipping_id

    delete_external_shipping_id(checkout)
    assert checkout.private_metadata == initial_private_metadata
