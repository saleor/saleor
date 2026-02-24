from decimal import Decimal
from unittest import mock

import graphene
from django.utils import timezone
from freezegun import freeze_time
from prices import Money
from promise import Promise

from ...shipping.interface import ExcludedShippingMethod, ShippingMethodData
from ...shipping.models import ShippingMethod
from ...webhook.transport.shipping_helpers import to_shipping_app_id
from ..delivery_context import (
    DeliveryMethodBase,
    assign_delivery_method_to_checkout,
    clear_cc_delivery_method,
    fetch_shipping_methods_for_checkout,
)
from ..fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
)
from ..models import CheckoutDelivery


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
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
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
    mocked_exclude_shipping_methods.return_value = Promise.resolve(
        [
            ExcludedShippingMethod(
                id=str(unavailable_shipping_method.id),
                reason=exclude_reason,
            )
        ]
    )

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
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
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

    mocked_webhook.return_value = Promise.resolve([available_shipping_method])

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
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
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

    mocked_webhook.return_value = Promise.resolve([available_shipping_method])

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
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
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

    mocked_webhook.return_value = Promise.resolve([available_shipping_method])

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
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
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

    mocked_webhook.return_value = Promise.resolve([available_shipping_method])

    checkout = checkout_with_item
    expired_app_id = to_shipping_app_id(external_app, "expired-shipping-method-id")
    assigned_delivery = checkout.shipping_methods.create(
        external_shipping_method_id=expired_app_id,
        name="Old External Shipping name",
        price_amount=Decimal(99),
        currency="USD",
        is_external=True,
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
    "saleor.checkout.webhooks.exclude_shipping.excluded_shipping_methods_for_checkout"
)
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
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
    mocked_exclude_shipping_methods.return_value = Promise.resolve(
        [
            ExcludedShippingMethod(
                id=str(unavailable_shipping_method.id),
                reason=exclude_reason,
            )
        ]
    )

    mocked_list_shipping_methods.return_value = Promise.resolve(
        [unavailable_shipping_method]
    )

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
@mock.patch(
    "saleor.checkout.webhooks.list_shipping_methods.list_shipping_methods_for_checkout"
)
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

    mocked_webhook.return_value = Promise.resolve([available_shipping_method])

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


def test_assign_delivery_method_to_checkout_delivery_method_to_none(
    checkout_with_delivery_method_for_cc, plugins_manager
):
    # given
    checkout = checkout_with_delivery_method_for_cc

    lines_info, _ = fetch_checkout_lines(checkout)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)

    # when
    assign_delivery_method_to_checkout(checkout_info, lines_info, plugins_manager, None)

    # then
    assert checkout_with_delivery_method_for_cc.collection_point_id is None
    assert checkout_with_delivery_method_for_cc.shipping_address_id is None
    assert checkout_info.collection_point is None


def test_assign_delivery_method_to_checkout_delivery_method_to_external(
    checkout_with_shipping_method, shipping_app, plugins_manager
):
    # given
    checkout = checkout_with_shipping_method

    lines_info, _ = fetch_checkout_lines(checkout)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)

    app_shipping_id = "abcd"
    app_shipping_name = "Shipping"
    method_id = graphene.Node.to_global_id(
        "app", f"{shipping_app.id}:{app_shipping_id}"
    )

    shipping_method = CheckoutDelivery.objects.create(
        checkout=checkout,
        external_shipping_method_id=method_id,
        name=app_shipping_name,
        price_amount="10.00",
        currency="USD",
        maximum_delivery_days=7,
        is_external=True,
    )

    # when
    assign_delivery_method_to_checkout(
        checkout_info, lines_info, plugins_manager, shipping_method
    )

    # then
    assert checkout.shipping_method_name == app_shipping_name
    assert checkout.assigned_delivery.shipping_method_id == method_id
    assert checkout.assigned_delivery.name == app_shipping_name
    assert checkout_info.collection_point is None


def test_assign_delivery_method_to_checkout_delivery_method_to_cc(
    checkout,
    shipping_method_weight_based,
    warehouses_for_cc,
    checkout_delivery,
    plugins_manager,
):
    # given
    checkout.assigned_delivery = checkout_delivery(
        checkout, shipping_method_weight_based
    )
    checkout.shipping_method_name = shipping_method_weight_based.name

    lines_info, _ = fetch_checkout_lines(checkout)

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)

    collection_point = warehouses_for_cc[0]

    # when
    assign_delivery_method_to_checkout(
        checkout_info, lines_info, plugins_manager, collection_point
    )

    # then
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.assigned_delivery is None
    assert checkout.shipping_method_name is None


def test_clear_cc_delivery_method(
    checkout_with_delivery_method_for_cc, plugins_manager
):
    # given
    assert checkout_with_delivery_method_for_cc.collection_point_id

    checkout_info = fetch_checkout_info(
        checkout_with_delivery_method_for_cc, [], plugins_manager
    )

    # when
    clear_cc_delivery_method(checkout_info)

    # then
    checkout_with_delivery_method_for_cc.refresh_from_db()
    assert not checkout_with_delivery_method_for_cc.collection_point_id
    assert isinstance(checkout_info.get_delivery_method_info(), DeliveryMethodBase)


def test_is_valid_delivery_method(
    checkout_with_item, address, shipping_zone, checkout_delivery, plugins_manager
):
    checkout = checkout_with_item
    checkout.shipping_address = address
    checkout.save()

    lines, _ = fetch_checkout_lines(checkout)
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    delivery_method_info = checkout_info.get_delivery_method_info()
    # no shipping method assigned
    assert not delivery_method_info.is_valid_delivery_method()

    checkout.assigned_delivery = checkout_delivery(checkout)
    checkout.save()
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    delivery_method_info = checkout_info.get_delivery_method_info()

    assert delivery_method_info.is_valid_delivery_method()

    checkout.assigned_delivery.active = False
    checkout.assigned_delivery.save()
    checkout_info = fetch_checkout_info(checkout, lines, plugins_manager)
    delivery_method_info = checkout_info.get_delivery_method_info()

    assert not delivery_method_info.is_method_in_valid_methods(checkout_info)
