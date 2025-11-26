from decimal import Decimal
from unittest import mock

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
from ..models import CheckoutDelivery


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
    checkout_delivery: CheckoutDelivery,
    available_shipping_method: ShippingMethod,
    checkout,
    settings,
):
    shipping_listing = available_shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )

    assert isinstance(checkout_delivery, CheckoutDelivery)
    assert checkout_delivery.checkout_id == checkout.pk
    assert checkout_delivery.built_in_shipping_method_id == available_shipping_method.id
    assert checkout_delivery.name == available_shipping_method.name
    assert checkout_delivery.price_amount == shipping_listing.price_amount
    assert checkout_delivery.currency == shipping_listing.price.currency
    assert str(checkout_delivery.description) == str(
        available_shipping_method.description
    )
    assert (
        checkout_delivery.minimum_delivery_days
        == available_shipping_method.minimum_delivery_days
    )
    assert (
        checkout_delivery.maximum_delivery_days
        == available_shipping_method.maximum_delivery_days
    )
    assert checkout_delivery.active is True
    assert checkout_delivery.is_valid is True
    assert checkout_delivery.is_external is False
    assert checkout_delivery.tax_class_id == available_shipping_method.tax_class_id
    assert checkout_delivery.tax_class_name == available_shipping_method.tax_class.name
    assert (
        checkout_delivery.tax_class_metadata
        == available_shipping_method.tax_class.metadata
    )
    assert (
        checkout_delivery.tax_class_private_metadata
        == available_shipping_method.tax_class.private_metadata
    )

    checkout.refresh_from_db()
    assert (
        checkout.delivery_methods_stale_at
        == timezone.now() + settings.CHECKOUT_DELIVERY_OPTIONS_TTL
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_with_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    CheckoutDelivery.objects.all().delete()

    available_shipping_method = ShippingMethod.objects.get()
    assert available_shipping_method.tax_class

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
    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)
    assert checkout.shipping_methods.count() == 1
    # Make sure that shipping method data is aligned with the built-in shipping method
    _assert_built_in_shipping_method(
        checkout_delivery, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_updates_existing_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings, tax_class_zero_rates
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = (
        timezone.now() - settings.CHECKOUT_DELIVERY_OPTIONS_TTL
    )
    checkout.assigned_delivery_id = None
    checkout.save(
        update_fields=[
            "shipping_address",
            "delivery_methods_stale_at",
            "assigned_delivery_id",
        ]
    )

    available_shipping_method = ShippingMethod.objects.get()

    existing_shipping_method = checkout.shipping_methods.create(
        built_in_shipping_method_id=available_shipping_method.id,
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
    available_shipping_method.tax_class = tax_class_zero_rates
    available_shipping_method.save()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    # Confirm that we updated the shipping method instead of creating a new one
    assert len(shipping_methods) == 1
    assert CheckoutDelivery.objects.count() == 1
    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)
    assert existing_shipping_method.id == checkout_delivery.id

    # Make sure that shipping method data has been updated to align with the built-in shipping method
    _assert_built_in_shipping_method(
        checkout_delivery, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_removes_non_applicable_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = (
        timezone.now() + settings.CHECKOUT_DELIVERY_OPTIONS_TTL
    )
    checkout.save(update_fields=["shipping_address", "delivery_methods_stale_at"])

    available_shipping_method = ShippingMethod.objects.get()

    non_applicable_shipping_method_id = available_shipping_method.id + 1
    checkout.shipping_methods.create(
        built_in_shipping_method_id=non_applicable_shipping_method_id,
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
    assert CheckoutDelivery.objects.count() == 1
    assert len(shipping_methods) == 1
    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)

    # Confirms that the non-applicable shipping method was removed and the
    # new one was created
    _assert_built_in_shipping_method(
        checkout_delivery, available_shipping_method, checkout, settings
    )


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_non_applicable_assigned_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = (
        timezone.now() + settings.CHECKOUT_DELIVERY_OPTIONS_TTL
    )
    checkout.save(update_fields=["shipping_address", "delivery_methods_stale_at"])

    available_shipping_method = ShippingMethod.objects.get()

    non_applicable_shipping_method_id = available_shipping_method.id + 1
    assigned_delivery = checkout.shipping_methods.create(
        built_in_shipping_method_id=non_applicable_shipping_method_id,
        name="Nonexisting Shipping Method",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert CheckoutDelivery.objects.count() == 2
    assert len(shipping_methods) == 1

    new_checkout_delivery = shipping_methods[0]
    assigned_delivery = CheckoutDelivery.objects.get(is_valid=False)

    # Assigned shipping method is never removed explicitly but marked as invalid
    assert assigned_delivery.is_valid is False
    assert (
        assigned_delivery.built_in_shipping_method_id
        == assigned_delivery.built_in_shipping_method_id
    )
    assert checkout.assigned_delivery_id == assigned_delivery.id

    # Confirm that new shipping method was created
    _assert_built_in_shipping_method(
        new_checkout_delivery, available_shipping_method, checkout, settings
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
    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)
    assert checkout.shipping_methods.count() == 1
    assert checkout_delivery.active is False
    assert checkout_delivery.message == exclude_reason


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_with_changed_price_of_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    CheckoutDelivery.objects.all().delete()

    available_shipping_method = ShippingMethod.objects.get()
    shipping_channel_listing = available_shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )
    previous_shipping_price = shipping_channel_listing.price_amount

    assigned_delivery = checkout.shipping_methods.create(
        built_in_shipping_method_id=available_shipping_method.id,
        name="Nonexisting Shipping Method",
        price_amount=previous_shipping_price,
        currency="USD",
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    # Change the price of the shipping method in channel listing
    new_shipping_price_amount = previous_shipping_price + Decimal(10)
    shipping_channel_listing.price_amount = new_shipping_price_amount
    shipping_channel_listing.save(update_fields=["price_amount"])

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    fetch_shipping_methods_for_checkout(checkout_info)

    # then
    checkout.refresh_from_db()
    assigned_delivery.refresh_from_db()
    assert checkout.assigned_delivery_id == assigned_delivery.id

    # Changing the price of shipping method assigned to checkout
    # caused that after fetching shipping methods, the checkout
    # prices are marked as expired.
    assert checkout.price_expiration == timezone.now()

    # The assigned shipping method has updated price
    assert assigned_delivery.price_amount == new_shipping_price_amount


@freeze_time("2024-05-31 12:00:01")
def test_fetch_shipping_methods_for_checkout_with_changed_tax_class_of_built_in_shipping_method(
    checkout_with_item, plugins_manager, address, settings, tax_class_zero_rates
):
    # given
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save(update_fields=["shipping_address"])

    CheckoutDelivery.objects.all().delete()

    available_shipping_method = ShippingMethod.objects.get()
    shipping_channel_listing = available_shipping_method.channel_listings.get(
        channel_id=checkout.channel_id
    )
    previous_shipping_price = shipping_channel_listing.price_amount

    assigned_delivery = checkout.shipping_methods.create(
        built_in_shipping_method_id=available_shipping_method.id,
        name="Nonexisting Shipping Method",
        price_amount=previous_shipping_price,
        currency="USD",
        tax_class_id=available_shipping_method.tax_class_id,
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    assert available_shipping_method.tax_class != tax_class_zero_rates
    available_shipping_method.tax_class = tax_class_zero_rates
    available_shipping_method.save()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    fetch_shipping_methods_for_checkout(checkout_info)

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery_id == assigned_delivery.id

    # Changing the tax class of shipping method assigned to checkout
    # caused that after fetching shipping methods, the checkout
    # prices are marked as expired.
    assert checkout.price_expiration == timezone.now()


def _assert_external_shipping_method(
    checkout_delivery: CheckoutDelivery,
    available_shipping_method: ShippingMethodData,
    checkout,
    settings,
):
    assert checkout_delivery.checkout_id == checkout.pk
    assert checkout_delivery.external_shipping_method_id == available_shipping_method.id
    assert checkout_delivery.name == available_shipping_method.name
    assert checkout_delivery.price_amount == available_shipping_method.price.amount
    assert checkout_delivery.currency == available_shipping_method.price.currency
    assert checkout_delivery.description == str(available_shipping_method.description)
    assert (
        checkout_delivery.minimum_delivery_days
        == available_shipping_method.minimum_delivery_days
    )
    assert (
        checkout_delivery.maximum_delivery_days
        == available_shipping_method.maximum_delivery_days
    )
    assert checkout_delivery.active == available_shipping_method.active
    assert checkout_delivery.is_valid is True
    assert checkout_delivery.is_external is True
    checkout.refresh_from_db()
    assert (
        checkout.delivery_methods_stale_at
        == timezone.now() + settings.CHECKOUT_DELIVERY_OPTIONS_TTL
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
    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)

    # Make sure that shipping method data is aligned with the external shipping method
    _assert_external_shipping_method(
        checkout_delivery, available_shipping_method, checkout, settings
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
        external_shipping_method_id=to_shipping_app_id(
            app, "external-shipping-method-id"
        ),
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.save(update_fields=["shipping_address", "delivery_methods_stale_at"])

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert len(shipping_methods) == 1

    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)
    # Make sure that shipping method data has been updated to align with the
    # external shipping method
    _assert_external_shipping_method(
        checkout_delivery, available_shipping_method, checkout, settings
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
        external_shipping_method_id=to_shipping_app_id(
            external_app, "expired-shipping-method-id"
        ),
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.save(update_fields=["shipping_address", "delivery_methods_stale_at"])

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert len(shipping_methods) == 1

    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)
    # Confirms that the non-applicable shipping method was removed and the
    # new one was created
    _assert_external_shipping_method(
        checkout_delivery, available_shipping_method, checkout, settings
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
    expired_app_id = to_shipping_app_id(external_app, "expired-shipping-method-id")
    assigned_delivery = checkout.shipping_methods.create(
        external_shipping_method_id=expired_app_id,
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
    )
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    shipping_methods = fetch_shipping_methods_for_checkout(checkout_info)

    # then
    assert CheckoutDelivery.objects.count() == 2
    assert len(shipping_methods) == 1

    new_checkout_delivery = shipping_methods[0]
    assigned_delivery = CheckoutDelivery.objects.get(is_valid=False)

    checkout.refresh_from_db()
    # Assigned shipping method is never removed explicitly but marked as invalid
    assert assigned_delivery.is_valid is False
    assert assigned_delivery.external_shipping_method_id == expired_app_id
    assert checkout.assigned_delivery_id == assigned_delivery.id

    # Confirm that new shipping method was created
    _assert_external_shipping_method(
        new_checkout_delivery, available_shipping_method, checkout, settings
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
    checkout_delivery = shipping_methods[0]
    assert isinstance(checkout_delivery, CheckoutDelivery)

    assert checkout_delivery.active is False
    assert checkout_delivery.message == exclude_reason


@freeze_time("2024-05-31 12:00:01")
@mock.patch("saleor.plugins.manager.PluginsManager.list_shipping_methods_for_checkout")
def test_fetch_shipping_methods_for_checkout_with_changed_price_of_external_shipping_method(
    mocked_webhook,
    checkout_with_item,
    plugins_manager,
    address,
    app,
    settings,
):
    # given
    shipping_price_amount = Decimal(10)

    available_shipping_method = ShippingMethodData(
        id=to_shipping_app_id(app, "external-shipping-method-id"),
        price=Money(shipping_price_amount, checkout_with_item.currency),
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

    new_shipping_price_amount = shipping_price_amount + Decimal(99)
    checkout = checkout_with_item
    assigned_delivery = checkout.shipping_methods.create(
        external_shipping_method_id=to_shipping_app_id(
            app, "external-shipping-method-id"
        ),
        name="External Shipping name",
        price_amount=new_shipping_price_amount,
        currency="USD",
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.shipping_address = address
    checkout.delivery_methods_stale_at = timezone.now()
    checkout.save()

    ShippingMethod.objects.all().delete()

    lines_info, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(
        checkout, lines=lines_info, manager=plugins_manager
    )

    # when
    fetch_shipping_methods_for_checkout(checkout_info)

    # then
    checkout.refresh_from_db()
    assert checkout.assigned_delivery_id == assigned_delivery.id
    # Changing the price of shipping method assigned to checkout
    # caused that after fetching shipping methods, the checkout
    # prices are marked as expired.
    assert checkout.price_expiration == timezone.now()

    # The assigned shipping method has updated price
    assert assigned_delivery.price_amount == new_shipping_price_amount
