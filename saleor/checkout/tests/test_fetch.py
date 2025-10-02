from decimal import Decimal
from unittest import mock

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time
from prices import Money

from ...plugins.base_plugin import ExcludedShippingMethod
from ...product.models import ProductChannelListing, ProductVariantChannelListing
from ...shipping.interface import ShippingMethodData
from ...shipping.models import ShippingMethod
from ...webhook.transport.shipping_helpers import to_shipping_app_id
from ..fetch import (
    CheckoutLineInfo,
    fetch_checkout_info,
    fetch_checkout_lines,
    fetch_shipping_methods_for_checkout,
)
from ..models import CheckoutShippingMethod


def test_checkout_line_info_undiscounted_unit_price(checkout_with_item_on_promotion):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_variant_price = variant_channel_listing.price

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert checkout_line_info.undiscounted_unit_price == expected_variant_price


def test_checkout_line_info_undiscounted_unit_price_without_listing(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    expected_variant_price = variant_channel_listing.price

    variant.channel_listings.all().delete()

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=None,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert checkout_line_info.undiscounted_unit_price == expected_variant_price


def test_checkout_line_info_undiscounted_unit_price_when_listing_without_price(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    expected_variant_price = variant_channel_listing.price

    variant_channel_listing.price_amount = None
    variant_channel_listing.save(update_fields=["price_amount"])

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=None,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert checkout_line_info.undiscounted_unit_price == expected_variant_price


def test_checkout_line_info_variant_discounted_price(checkout_with_item_on_promotion):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert (
        checkout_line_info.variant_discounted_price == expected_discounted_variant_price
    )


def test_checkout_line_info_variant_discounted_price_without_listing(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    variant.channel_listings.all().delete()

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=None,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert (
        checkout_line_info.variant_discounted_price == expected_discounted_variant_price
    )


def test_checkout_line_info_variant_discounted_price_when_listing_without_price(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()

    expected_discounted_variant_price = variant_channel_listing.discounted_price
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    variant_channel_listing.discounted_price_amount = None
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )
    # then
    assert (
        checkout_line_info.variant_discounted_price == expected_discounted_variant_price
    )


def test_checkout_line_info_variant_discounted_price_with_price_override(
    checkout_with_item_on_promotion,
):
    # given
    checkout_line = checkout_with_item_on_promotion.lines.first()
    channel = checkout_with_item_on_promotion.channel
    variant = checkout_line.variant
    variant_channel_listing = variant.channel_listings.get(channel_id=channel.id)
    product = variant.product
    product_type = product.product_type
    discounts = checkout_line.discounts.all()
    checkout_line.price_override = Decimal(5)
    checkout_line.save(update_fields=["price_override"])

    expected_discounted_variant_price = checkout_line.price_override
    assert variant_channel_listing.discounted_price != variant_channel_listing.price

    # when
    checkout_line_info = CheckoutLineInfo(
        line=checkout_line,
        variant=variant,
        channel_listing=variant_channel_listing,
        product=product,
        product_type=product_type,
        collections=[],
        tax_class=product.tax_class or product_type.tax_class,
        discounts=discounts,
        rules_info=[],
        channel=channel,
        voucher=None,
        voucher_code=None,
    )

    # then
    assert checkout_line_info.variant_discounted_price == Money(
        expected_discounted_variant_price, checkout_line.currency
    )


def test_fetch_checkout_lines_info(checkout_with_item_on_promotion):
    # given
    lines = list(checkout_with_item_on_promotion.lines.all())

    # when
    line_infos, unavailable_variants = fetch_checkout_lines(
        checkout_with_item_on_promotion
    )

    # then
    assert len(line_infos) == len(lines) == 1
    line_info = line_infos[0]
    line = lines[0]
    assert line_info.line.pk == line.pk
    assert not unavailable_variants


def test_fetch_checkout_lines_info_when_product_not_available(
    checkout_with_item_on_promotion,
):
    # given
    lines = list(checkout_with_item_on_promotion.lines.all())
    line = lines[0]
    line.variant.product.channel_listings.update(is_published=False)

    # when
    line_infos, unavailable_variants = fetch_checkout_lines(
        checkout_with_item_on_promotion
    )

    # then
    assert len(line_infos) == 1
    assert line_infos[0].line.pk == line.pk
    assert unavailable_variants == [line.variant_id]


@pytest.mark.parametrize(
    ("channel_listing_model", "listing_filter_field"),
    [
        (ProductVariantChannelListing, "variant_id"),
        (ProductChannelListing, "product__variants__id"),
    ],
)
def test_fetch_checkout_lines_info_when_line_without_channel_listing(
    channel_listing_model,
    listing_filter_field,
    checkout_with_item_on_promotion,
):
    # given
    lines = list(checkout_with_item_on_promotion.lines.all())
    line = lines[0]

    channel_listing_model.objects.filter(
        channel_id=checkout_with_item_on_promotion.channel_id,
        **{listing_filter_field: line.variant_id},
    ).delete()

    # when
    line_infos, unavailable_variants = fetch_checkout_lines(
        checkout_with_item_on_promotion
    )

    # then
    assert len(line_infos) == len(lines) == 1
    line_info = line_infos[0]
    line = lines[0]
    assert line_info.line.pk == line.pk
    assert unavailable_variants == [line.variant_id]


def test_fetch_checkout_lines_info_when_variant_channel_listing_without_price(
    checkout_with_item_on_promotion,
):
    # given
    lines = list(checkout_with_item_on_promotion.lines.all())
    line = lines[0]

    variant_channel_listing = line.variant.channel_listings.get(
        channel_id=checkout_with_item_on_promotion.channel_id
    )

    variant_channel_listing.price_amount = None
    variant_channel_listing.save(update_fields=["price_amount"])

    # when
    line_infos, unavailable_variants = fetch_checkout_lines(
        checkout_with_item_on_promotion
    )

    # then
    assert len(line_infos) == len(lines) == 1
    line_info = line_infos[0]
    line = lines[0]
    assert line_info.line.pk == line.pk
    assert unavailable_variants == [line.variant_id]


def _assert_built_in_shipping_method(
    checkout_shipping_method: CheckoutShippingMethod,
    available_shipping_method: ShippingMethod,
    checkout,
    settings,
):
    shipping_listing = available_shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )

    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)
    assert checkout_shipping_method.checkout_id == checkout.pk
    assert checkout_shipping_method.original_id == graphene.Node.to_global_id(
        "ShippingMethod", available_shipping_method.id
    )
    assert checkout_shipping_method.name == available_shipping_method.name
    assert checkout_shipping_method.price_amount == shipping_listing.price_amount
    assert checkout_shipping_method.currency == shipping_listing.price.currency
    assert str(checkout_shipping_method.description) == str(
        available_shipping_method.description
    )
    assert (
        checkout_shipping_method.minimum_delivery_days
        == available_shipping_method.minimum_delivery_days
    )
    assert (
        checkout_shipping_method.maximum_delivery_days
        == available_shipping_method.maximum_delivery_days
    )
    assert checkout_shipping_method.active is True
    assert checkout_shipping_method.is_valid is True
    assert checkout_shipping_method.is_external is False

    checkout.refresh_from_db()
    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_with_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    available_shipping_method = ShippingMethod.objects.get()
    available_shipping_method.description = {
        "time": 1759214012137,
        "blocks": [
            {
                "id": "fQMbdjz2Yt",
                "data": {"text": "<b>This is Shipping description</b>"},
                "type": "paragraph",
            }
        ],
        "version": "2.31.0-rc.7",
    }
    available_shipping_method.minimum_delivery_days = 5
    available_shipping_method.maximum_delivery_days = 10
    available_shipping_method.metadata = {
        "key": "value",
    }
    available_shipping_method.private_metadata = {
        "private_key": "private_value",
    }
    available_shipping_method.save()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    # Confirm that new shipping method was created
    assert len(shipping_methods) == 1
    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)
    assert checkout.shipping_methods.count() == 1
    # Make sure that shipping method data is aligned with the built-in shipping method
    _assert_built_in_shipping_method(
        checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_updates_existing_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_methods_stale_at = timezone.now()
    checkout.save(update_fields=["shipping_address", "shipping_methods_stale_at"])

    available_shipping_method = ShippingMethod.objects.get()

    existing_shipping_method = checkout.shipping_methods.create(
        original_id=graphene.Node.to_global_id(
            "ShippingMethod", available_shipping_method.id
        ),
        name=available_shipping_method.name,
        description=available_shipping_method.description,
        price_amount=Decimal(99),
        currency="USD",
        maximum_delivery_days=available_shipping_method.maximum_delivery_days,
        minimum_delivery_days=available_shipping_method.minimum_delivery_days,
        metadata=available_shipping_method.metadata,
        private_metadata=available_shipping_method.private_metadata,
        active=True,
        message=None,
        is_valid=True,
        is_external=False,
    )

    available_shipping_method.description = {
        "time": 1759214012137,
        "blocks": [
            {
                "id": "fQMbdjz2Yt",
                "data": {"text": "<b>This is Shipping description</b>"},
                "type": "paragraph",
            }
        ],
        "version": "2.31.0-rc.7",
    }
    available_shipping_method.minimum_delivery_days = 5
    available_shipping_method.maximum_delivery_days = 10
    available_shipping_method.metadata = {
        "key": "value",
    }
    available_shipping_method.private_metadata = {
        "private_key": "private_value",
    }
    available_shipping_method.save()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    # Confirm that we updated the shipping method instead of creating a new one
    assert CheckoutShippingMethod.objects.count() == 1
    assert len(shipping_methods) == 1
    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)
    assert existing_shipping_method.id == checkout_shipping_method.id

    # Make sure that shipping method data has been updated to align with the built-in shipping method
    _assert_built_in_shipping_method(
        checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_removes_non_applicable_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_methods_stale_at = (
        timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )
    checkout.save(update_fields=["shipping_address", "shipping_methods_stale_at"])

    available_shipping_method = ShippingMethod.objects.get()

    non_applicable_shipping_method_id = available_shipping_method.id + 1
    checkout.shipping_methods.create(
        original_id=graphene.Node.to_global_id(
            "ShippingMethod", non_applicable_shipping_method_id
        ),
        name="Nonexisting Shipping Method",
        price_amount=Decimal(99),
        currency="USD",
    )

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert CheckoutShippingMethod.objects.count() == 1
    assert len(shipping_methods) == 1
    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)

    # Confirms that the non-applicable shipping method was removed and the
    # new one was created
    _assert_built_in_shipping_method(
        checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_non_applicable_assigned_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.shipping_methods_stale_at = (
        timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )
    checkout.save(update_fields=["shipping_address", "shipping_methods_stale_at"])

    available_shipping_method = ShippingMethod.objects.get()

    non_applicable_shipping_method_id = available_shipping_method.id + 1
    assigned_shipping_method = checkout.shipping_methods.create(
        original_id=graphene.Node.to_global_id(
            "ShippingMethod", non_applicable_shipping_method_id
        ),
        name="Nonexisting Shipping Method",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.assigned_shipping_method = assigned_shipping_method
    checkout.save()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert CheckoutShippingMethod.objects.count() == 2
    assert len(shipping_methods) == 1

    new_checkout_shipping_method = shipping_methods[0]
    assigned_shipping_method = CheckoutShippingMethod.objects.get(is_valid=False)

    # Assigned shipping method is never removed explicitly but marked as invalid
    assert assigned_shipping_method.is_valid is False
    assert assigned_shipping_method.original_id == assigned_shipping_method.original_id
    assert checkout.assigned_shipping_method_id == assigned_shipping_method.id

    # Confirm that new shipping method was created
    _assert_built_in_shipping_method(
        new_checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
def test_fetch_shipping_methods_for_checkout_with_excluded_built_in_shipping_method(
    mocked_exclude_shipping_methods,
    checkout_with_item,
    plugins_manager,
    address,
    settings,
):
    # given
    unavailable_shipping_method = ShippingMethod.objects.get()
    exclude_reason = "This shipping method is not available."
    mocked_exclude_shipping_methods.return_value = [
        ExcludedShippingMethod(
            id=str(unavailable_shipping_method.id),
            reason=exclude_reason,
        )
    ]

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert len(shipping_methods) == 1
    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)
    assert checkout.shipping_methods.count() == 1
    assert checkout_shipping_method.active is False
    assert checkout_shipping_method.message == exclude_reason


def _assert_external_shipping_method(
    checkout_shipping_method: CheckoutShippingMethod,
    available_shipping_method: ShippingMethodData,
    checkout,
    settings,
):
    assert checkout_shipping_method.checkout_id == checkout.pk
    assert checkout_shipping_method.original_id == available_shipping_method.id
    assert checkout_shipping_method.name == available_shipping_method.name
    assert (
        checkout_shipping_method.price_amount == available_shipping_method.price.amount
    )
    assert checkout_shipping_method.currency == available_shipping_method.price.currency
    assert checkout_shipping_method.description == str(
        available_shipping_method.description
    )
    assert (
        checkout_shipping_method.minimum_delivery_days
        == available_shipping_method.minimum_delivery_days
    )
    assert (
        checkout_shipping_method.maximum_delivery_days
        == available_shipping_method.maximum_delivery_days
    )
    assert checkout_shipping_method.active == available_shipping_method.active
    assert checkout_shipping_method.is_valid is True
    assert checkout_shipping_method.is_external is True
    checkout.refresh_from_db()
    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )


@freeze_time("2024-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.list_shipping_methods_for_checkout")
def test_fetch_shipping_methods_for_checkout_with_external_shipping_method(
    mocked_webhook,
    checkout_with_item,
    plugins_manager,
    address,
    app,
    settings,
):
    # given
    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-shipping-method-id"),
        price=Money(Decimal(10), checkout_with_item.currency),
        active=False,
        name="External Shipping",
        description="External Shipping Description",
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={
            "key": "value",
        },
    )

    mocked_webhook.return_value = [available_shipping_method]

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    # Confirms that new shipping method was created
    assert len(shipping_methods) == 1
    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)

    # Make sure that shipping method data is aligned with the external shipping method
    _assert_external_shipping_method(
        checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.list_shipping_methods_for_checkout")
def test_fetch_shipping_methods_for_checkout_updates_existing_external_shipping_method(
    mocked_webhook,
    checkout_with_item,
    plugins_manager,
    address,
    app,
    settings,
):
    # given
    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-shipping-method-id"),
        price=Money(Decimal(10), checkout_with_item.currency),
        active=False,
        name="External Shipping",
        description="External Shipping Description",
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={
            "key": "value",
        },
    )

    mocked_webhook.return_value = [available_shipping_method]

    checkout = checkout_with_item
    checkout.shipping_methods.create(
        original_id=to_shipping_app_id(app, "external-shipping-method-id"),
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.shipping_address = address
    checkout.shipping_methods_stale_at = timezone.now()
    checkout.save(update_fields=["shipping_address", "shipping_methods_stale_at"])

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert len(shipping_methods) == 1

    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)
    # Make sure that shipping method data has been updated to align with the
    # external shipping method
    _assert_external_shipping_method(
        checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.list_shipping_methods_for_checkout")
def test_fetch_shipping_methods_for_checkout_removes_non_applicable_external_shipping_method(
    mocked_webhook,
    checkout_with_item,
    plugins_manager,
    address,
    app,
    external_app,
    settings,
):
    # given
    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-shipping-method-id"),
        price=Money(Decimal(10), checkout_with_item.currency),
        active=False,
        name="External Shipping",
        description="External Shipping Description",
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={
            "key": "value",
        },
    )

    mocked_webhook.return_value = [available_shipping_method]

    checkout = checkout_with_item
    checkout.shipping_methods.create(
        original_id=to_shipping_app_id(external_app, "expired-shipping-method-id"),
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.shipping_address = address
    checkout.shipping_methods_stale_at = timezone.now()
    checkout.save(update_fields=["shipping_address", "shipping_methods_stale_at"])

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert len(shipping_methods) == 1

    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)
    # Confirms that the non-applicable shipping method was removed and the
    # new one was created
    _assert_external_shipping_method(
        checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.list_shipping_methods_for_checkout")
def test_fetch_shipping_methods_for_checkout_non_applicable_assigned_external_shipping_method(
    mocked_webhook,
    checkout_with_item,
    plugins_manager,
    address,
    app,
    external_app,
    settings,
):
    # given
    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-shipping-method-id"),
        price=Money(Decimal(10), checkout_with_item.currency),
        active=False,
        name="External Shipping",
        description="External Shipping Description",
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={
            "key": "value",
        },
    )

    mocked_webhook.return_value = [available_shipping_method]

    checkout = checkout_with_item
    assigned_shipping_method = checkout.shipping_methods.create(
        original_id=to_shipping_app_id(external_app, "expired-shipping-method-id"),
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.shipping_address = address
    checkout.shipping_methods_stale_at = timezone.now()
    checkout.assigned_shipping_method = assigned_shipping_method
    checkout.save()

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert CheckoutShippingMethod.objects.count() == 2
    assert len(shipping_methods) == 1

    new_checkout_shipping_method = shipping_methods[0]
    assigned_shipping_method = CheckoutShippingMethod.objects.get(is_valid=False)

    checkout.refresh_from_db()
    # Assigned shipping method is never removed explicitly but marked as invalid
    assert assigned_shipping_method.is_valid is False
    assert assigned_shipping_method.original_id == assigned_shipping_method.original_id
    assert checkout.assigned_shipping_method_id == assigned_shipping_method.id

    # Confirm that new shipping method was created
    _assert_external_shipping_method(
        new_checkout_shipping_method, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
@mock.patch(
    "saleor.plugins.manager.PluginsManager.excluded_shipping_methods_for_checkout"
)
@mock.patch("saleor.plugins.manager.PluginsManager.list_shipping_methods_for_checkout")
def test_fetch_shipping_methods_for_checkout_with_excluded_external_shipping_method(
    mocked_list_shipping_methods,
    mocked_exclude_shipping_methods,
    checkout_with_item,
    plugins_manager,
    address,
    app,
    settings,
):
    # given
    unavailable_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-shipping-method-id"),
        price=Money(Decimal(10), checkout_with_item.currency),
        active=False,
        name="External Shipping",
        description="External Shipping Description",
        maximum_delivery_days=10,
        minimum_delivery_days=5,
        metadata={
            "key": "value",
        },
    )
    exclude_reason = "This shipping method is not available."
    mocked_exclude_shipping_methods.return_value = [
        ExcludedShippingMethod(
            id=str(unavailable_shipping_method.id),
            reason=exclude_reason,
        )
    ]

    mocked_list_shipping_methods.return_value = [unavailable_shipping_method]

    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert len(shipping_methods) == 1
    checkout_shipping_method = shipping_methods[0]
    assert isinstance(checkout_shipping_method, CheckoutShippingMethod)

    assert checkout_shipping_method.active is False
    assert checkout_shipping_method.message == exclude_reason
