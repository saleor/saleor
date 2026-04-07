import json
from decimal import Decimal
from unittest.mock import Mock, patch

import graphene
import pytest
from prices import Money

from .....core.prices import quantize_price
from .....discount import DiscountType, RewardValueType
from .....discount.models import CheckoutDiscount, CheckoutLineDiscount
from .....plugins.manager import get_plugins_manager
from .....product.models import ProductVariantChannelListing
from .... import base_calculations
from ....fetch import fetch_checkout_info, fetch_checkout_lines
from ....models import CheckoutLine
from ....utils import add_voucher_to_checkout
from ....webhooks.calculate_taxes import (
    generate_checkout_payload_for_tax_calculation,
)


@pytest.fixture
def mocked_fetch_checkout():
    def mocked_fetch_side_effect(
        checkout_info, manager, lines, address, force_update=False
    ):
        return checkout_info, lines

    with patch(
        "saleor.checkout.calculations.fetch_checkout_data",
        new=Mock(side_effect=mocked_fetch_side_effect),
    ) as mocked_fetch:
        yield mocked_fetch


@patch(
    "saleor.checkout.webhooks.calculate_taxes.serialize_checkout_lines_for_tax_calculation"
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_entire_order_voucher(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    voucher,
):
    checkout = checkout_with_prices
    currency = checkout.currency

    voucher.name = "Voucher 5 USD"
    voucher.save(update_fields=["name"])

    discount_amount = Decimal("5.00")
    checkout.voucher_code = voucher.code
    checkout.discount_amount = discount_amount
    checkout.discount_name = voucher.name
    checkout.save(update_fields=["voucher_code", "discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    shipping_price = str(
        quantize_price(
            checkout.assigned_delivery.price.amount,
            currency,
        )
    )
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [{"amount": str(discount_amount), "name": voucher.name}],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.assigned_delivery.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
        "shipping_amount": shipping_price,
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch(
    "saleor.checkout.webhooks.calculate_taxes.serialize_checkout_lines_for_tax_calculation"
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_specific_product_voucher(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    voucher_specific_product_type,
):
    checkout = checkout_with_prices
    currency = checkout.currency

    voucher = voucher_specific_product_type
    voucher.name = "Voucher 5 USD"
    voucher.save(update_fields=["name"])

    discount_amount = Decimal("5.00")
    checkout.voucher_code = voucher.code
    checkout.discount_amount = discount_amount
    checkout.discount_name = voucher.name
    checkout.save(update_fields=["voucher_code", "discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    shipping_price = str(
        quantize_price(
            checkout.assigned_delivery.price.amount,
            currency,
        )
    )
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.assigned_delivery.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
        "shipping_amount": shipping_price,
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch(
    "saleor.checkout.webhooks.calculate_taxes.serialize_checkout_lines_for_tax_calculation"
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_shipping_voucher(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_items_and_shipping,
    prices_entered_with_tax,
    voucher_shipping_type,
    customer_user,
):
    checkout = checkout_with_items_and_shipping
    checkout.user = customer_user
    currency = checkout.currency
    voucher = voucher_shipping_type
    voucher.countries = []
    voucher.save(update_fields=["countries"])

    shipping_price = checkout.assigned_delivery.price.amount
    assert shipping_price == Decimal(10)

    voucher_discount_amount = Decimal(3)
    listing = voucher.channel_listings.first()
    listing.discount_value = voucher_discount_amount
    listing.save(update_fields=["discount_value"])
    expected_shipping_price = quantize_price(
        shipping_price - voucher_discount_amount, currency
    )

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout, lines, manager)
    add_voucher_to_checkout(
        manager, checkout_info, lines, voucher, voucher.codes.first()
    )
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {},
        "shipping_name": checkout.assigned_delivery.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"key": "value"},
        "total_amount": str(
            quantize_price(
                base_calculations.base_checkout_total(checkout_info, lines).amount,
                currency,
            )
        ),
        "shipping_amount": str(expected_shipping_price),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch(
    "saleor.checkout.webhooks.calculate_taxes.serialize_checkout_lines_for_tax_calculation"
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_order_discount(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    order_promotion_rule,
):
    checkout = checkout_with_prices
    rule = order_promotion_rule
    currency = checkout.currency

    discount_amount = Decimal("5.00")
    CheckoutDiscount.objects.create(
        checkout=checkout,
        promotion_rule=rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=rule.reward_value_type,
        value=rule.reward_value,
        amount_value=discount_amount,
        currency=checkout.currency,
    )

    checkout.discount_amount = discount_amount
    checkout.discount_name = rule.name
    checkout.save(update_fields=["discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    subtotal_price = Money(0, currency)
    for line_info in lines:
        variant = line_info.variant
        variant_listing = line_info.channel_listing
        unit_price = variant.get_price(variant_listing)
        subtotal_price += unit_price * line_info.line.quantity
    shipping_price = quantize_price(
        checkout.assigned_delivery.price.amount,
        currency,
    )
    total_price_amount = subtotal_price.amount + shipping_price
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [{"amount": str(discount_amount), "name": rule.name}],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.assigned_delivery.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                total_price_amount,
                currency,
            )
        ),
        "shipping_amount": str(shipping_price),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch(
    "saleor.checkout.webhooks.calculate_taxes.serialize_checkout_lines_for_tax_calculation"
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_gift_promotion(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    gift_promotion_rule,
):
    checkout = checkout_with_prices
    currency = checkout.currency

    variants = gift_promotion_rule.gifts.all()
    variant_listings = ProductVariantChannelListing.objects.filter(variant__in=variants)
    top_price, variant_id = max(
        variant_listings.values_list("discounted_price_amount", "variant")
    )
    variant_listing = [
        listing for listing in variant_listings if listing.variant_id == variant_id
    ][0]

    line = CheckoutLine.objects.create(
        checkout=checkout,
        quantity=1,
        variant_id=variant_id,
        is_gift=True,
        currency="USD",
        undiscounted_unit_price_amount=variant_listing.price_amount,
    )

    CheckoutLineDiscount.objects.create(
        line=line,
        promotion_rule=gift_promotion_rule,
        type=DiscountType.ORDER_PROMOTION,
        value_type=RewardValueType.FIXED,
        value=top_price,
        amount_value=top_price,
        currency=checkout.channel.currency_code,
    )

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]

    # then
    subtotal_price = Money(0, currency)
    for line_info in lines:
        if line_info.line.is_gift:
            continue
        variant = line_info.variant
        variant_listing = line_info.channel_listing
        unit_price = variant.get_price(variant_listing)
        subtotal_price += unit_price * line_info.line.quantity
    shipping_price = quantize_price(
        checkout.assigned_delivery.price.amount,
        currency,
    )
    total_price_amount = subtotal_price.amount + shipping_price
    assert payload["discounts"] == []
    assert payload["total_amount"] == str(
        quantize_price(
            total_price_amount,
            currency,
        )
    )

    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )


@patch(
    "saleor.checkout.webhooks.calculate_taxes.serialize_checkout_lines_for_tax_calculation"
)
@pytest.mark.parametrize("prices_entered_with_tax", [True, False])
def test_generate_checkout_payload_for_tax_calculation_no_discount(
    mocked_serialize_checkout_lines_for_tax_calculation,
    mocked_fetch_checkout,
    checkout_with_prices,
    prices_entered_with_tax,
    order_promotion_rule,
):
    checkout = checkout_with_prices
    rule = order_promotion_rule
    currency = checkout.currency

    discount_amount = 0
    checkout.discount_amount = discount_amount
    checkout.discount_name = rule.name
    checkout.save(update_fields=["discount_amount", "discount_name"])

    tax_configuration = checkout.channel.tax_configuration
    tax_configuration.prices_entered_with_tax = prices_entered_with_tax
    tax_configuration.save(update_fields=["prices_entered_with_tax"])
    tax_configuration.country_exceptions.all().delete()

    mocked_serialized_checkout_lines = {"data": "checkout_lines_data"}
    mocked_serialize_checkout_lines_for_tax_calculation.return_value = (
        mocked_serialized_checkout_lines
    )

    # when
    lines, _ = fetch_checkout_lines(checkout_with_prices)
    manager = get_plugins_manager(allow_replica=False)
    checkout_info = fetch_checkout_info(checkout_with_prices, lines, manager)
    payload = json.loads(
        generate_checkout_payload_for_tax_calculation(checkout_info, lines)
    )[0]
    address = checkout.shipping_address

    # then
    subtotal_price = Money(0, currency)
    for line_info in lines:
        variant = line_info.variant
        variant_listing = line_info.channel_listing
        unit_price = variant.get_price(variant_listing)
        subtotal_price += unit_price * line_info.line.quantity
    shipping_price = quantize_price(
        checkout.assigned_delivery.price.amount,
        currency,
    )
    total_price_amount = subtotal_price.amount + shipping_price
    assert payload == {
        "type": "Checkout",
        "id": graphene.Node.to_global_id("Checkout", checkout.pk),
        "address": {
            "type": "Address",
            "id": graphene.Node.to_global_id("Address", address.pk),
            "first_name": address.first_name,
            "last_name": address.last_name,
            "company_name": address.company_name,
            "street_address_1": address.street_address_1,
            "street_address_2": address.street_address_2,
            "city": address.city,
            "city_area": address.city_area,
            "postal_code": address.postal_code,
            "country": address.country.code,
            "country_area": address.country_area,
            "phone": str(address.phone),
        },
        "channel": {
            "type": "Channel",
            "id": graphene.Node.to_global_id("Channel", checkout.channel_id),
            "currency_code": checkout.channel.currency_code,
            "slug": checkout.channel.slug,
        },
        "currency": currency,
        "discounts": [],
        "included_taxes_in_prices": prices_entered_with_tax,
        "lines": mocked_serialized_checkout_lines,
        "metadata": {"meta_key": "meta_value"},
        "shipping_name": checkout.assigned_delivery.name,
        "user_id": graphene.Node.to_global_id("User", checkout.user.pk),
        "user_public_metadata": {"user_public_meta_key": "user_public_meta_value"},
        "total_amount": str(
            quantize_price(
                total_price_amount,
                currency,
            )
        ),
        "shipping_amount": str(shipping_price),
    }
    mocked_fetch_checkout.assert_not_called()
    mocked_serialize_checkout_lines_for_tax_calculation.assert_called_once_with(
        checkout_info,
        lines,
    )
