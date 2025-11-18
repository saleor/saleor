from decimal import Decimal

from django.utils import timezone
from freezegun import freeze_time
from prices import Money

from ...checkout.models import CheckoutDelivery
from ...shipping.interface import ShippingMethodData
from ...webhook.transport.shipping_helpers import to_shipping_app_id
from ..utils import (
    PRIVATE_META_APP_SHIPPING_ID,
    assign_built_in_shipping_to_checkout,
    assign_collection_point_to_checkout,
    assign_external_shipping_to_checkout,
    get_external_shipping_id,
    remove_delivery_method_from_checkout,
    remove_external_shipping_from_checkout,
)


def test_remove_delivery_method_from_checkout_with_cc(
    checkout_with_delivery_method_for_cc,
):
    # given
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
    }
    # when
    updated_fields = remove_delivery_method_from_checkout(
        checkout_with_delivery_method_for_cc
    )

    # then
    assert expected_updated_fields == set(updated_fields)
    assert checkout_with_delivery_method_for_cc.collection_point_id is None
    assert checkout_with_delivery_method_for_cc.shipping_address_id is None


def test_remove_delivery_method_from_checkout_with_external_shipping(
    checkout_with_item,
):
    # given
    checkout_with_item.external_shipping_method_id = "abd"
    checkout_with_item.shipping_method_name = "Ext shipping"

    expected_updated_fields = {
        "shipping_method_name",
        "external_shipping_method_id",
        "shipping_methods_stale_at",
    }
    # when
    updated_fields = remove_delivery_method_from_checkout(checkout_with_item)

    # then
    assert expected_updated_fields == set(updated_fields)
    assert checkout_with_item.external_shipping_method_id is None
    assert checkout_with_item.shipping_method_name is None
    assert checkout_with_item.shipping_methods_stale_at is None


def test_remove_delivery_method_from_checkout_with_built_in_shipping(
    checkout_with_item, shipping_method
):
    # given
    checkout_with_item.shipping_method = shipping_method
    checkout_with_item.shipping_method_name = shipping_method.name

    expected_updated_fields = {
        "shipping_method_id",
        "shipping_method_name",
        "shipping_methods_stale_at",
    }
    # when
    updated_fields = remove_delivery_method_from_checkout(checkout_with_item)

    # then
    assert expected_updated_fields == set(updated_fields)
    assert checkout_with_item.shipping_method is None
    assert checkout_with_item.shipping_method_name is None
    assert checkout_with_item.shipping_methods_stale_at is None


def test_remove_delivery_method_from_checkout_without_method(checkout_with_item):
    # given
    expected_updated_fields = []

    # when
    updated_fields = remove_delivery_method_from_checkout(checkout_with_item)

    # then
    assert expected_updated_fields == updated_fields


@freeze_time("2023-01-01 12:00:00")
def test_assign_external_shipping_to_checkout_with_cc(
    checkout_with_delivery_method_for_cc, app, settings
):
    # given
    app_shipping_name = "Shipping"
    app_shipping_id = to_shipping_app_id(app, "abcd")
    external_shipping_data = ShippingMethodData(
        name=app_shipping_name, id=app_shipping_id, price=Money(0, "USD")
    )
    checkout = checkout_with_delivery_method_for_cc

    expected_updated_fields = {
        "external_shipping_method_id",
        "shipping_method_name",
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_updated = assign_external_shipping_to_checkout(
        checkout, external_shipping_data
    )

    # then
    assert expected_updated_fields == set(fields_to_updated)
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )
    assert checkout.external_shipping_method_id == app_shipping_id
    assert checkout.shipping_method_name == app_shipping_name
    assert checkout.collection_point_id is None
    assert checkout.shipping_address_id is None

    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assigned_delivery = checkout.assigned_delivery
    assert assigned_delivery.name == app_shipping_name
    assert assigned_delivery.external_shipping_method_id == app_shipping_id
    assert assigned_delivery.price.amount == Decimal(0)
    assert assigned_delivery.price.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_external_shipping_to_checkout_without_delivery_method(
    checkout, app, settings
):
    # given
    app_shipping_id = to_shipping_app_id(app, "abcd")
    app_shipping_name = "Shipping"
    external_shipping_data = ShippingMethodData(
        name=app_shipping_name, id=app_shipping_id, price=Money(0, "USD")
    )

    expected_updated_fields = {
        "external_shipping_method_id",
        "shipping_method_name",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_updated = assign_external_shipping_to_checkout(
        checkout, external_shipping_data
    )

    # then
    assert expected_updated_fields == set(fields_to_updated)
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )
    assert checkout.external_shipping_method_id == app_shipping_id
    assert checkout.shipping_method_name == app_shipping_name
    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assigned_delivery = checkout.assigned_delivery
    assert assigned_delivery.name == app_shipping_name
    assert assigned_delivery.external_shipping_method_id == app_shipping_id
    assert assigned_delivery.price.amount == Decimal(0)
    assert assigned_delivery.price.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_external_shipping_to_checkout_with_built_in_shipping(
    checkout_with_item, shipping_method, app, settings
):
    # given
    app_shipping_id = to_shipping_app_id(app, "abcd")
    app_shipping_name = "Shipping"
    external_shipping_data = ShippingMethodData(
        name=app_shipping_name, id=app_shipping_id, price=Money(0, "USD")
    )
    checkout_with_item.shipping_method = shipping_method
    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout_with_item,
        name=shipping_method.name,
        price_amount=Decimal("10.0"),
        currency=checkout_with_item.currency,
        built_in_shipping_method_id=shipping_method.id,
    )

    checkout_with_item.assigned_delivery = assigned_delivery
    checkout_with_item.save()

    checkout = checkout_with_item

    expected_updated_fields = {
        "external_shipping_method_id",
        "shipping_method_name",
        "shipping_method_id",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_updated = assign_external_shipping_to_checkout(
        checkout, external_shipping_data
    )

    # then
    assert expected_updated_fields == set(fields_to_updated)
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )
    assert checkout.external_shipping_method_id == app_shipping_id
    assert checkout.shipping_method_name == app_shipping_name
    assert checkout.shipping_method_id is None

    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assert checkout.assigned_delivery.id == assigned_delivery.id

    assigned_delivery.refresh_from_db()
    assert assigned_delivery.name == app_shipping_name
    assert assigned_delivery.external_shipping_method_id == app_shipping_id
    assert assigned_delivery.built_in_shipping_method_id is None
    assert assigned_delivery.price_amount == Decimal(0)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_external_shipping_to_checkout_with_different_external_shipping(
    checkout_with_item, app, settings
):
    # given
    app_shipping_id = to_shipping_app_id(app, "abcd")
    app_shipping_name = "Shipping"
    external_shipping_data = ShippingMethodData(
        name=app_shipping_name, id=app_shipping_id, price=Money(0, "USD")
    )
    checkout = checkout_with_item
    checkout.external_shipping_method_id = "different-shipp"
    checkout.shipping_method_name = "Ext shipping"

    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout_with_item,
        name=app_shipping_name,
        price_amount=Decimal("10.0"),
        currency=checkout_with_item.currency,
        external_shipping_method_id=checkout.external_shipping_method_id,
    )

    checkout_with_item.assigned_delivery = assigned_delivery
    checkout_with_item.save()

    expected_updated_fields = {
        "external_shipping_method_id",
        "shipping_method_name",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_updated = assign_external_shipping_to_checkout(
        checkout, external_shipping_data
    )

    # then
    assert expected_updated_fields == set(fields_to_updated)
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )
    assert checkout.external_shipping_method_id == app_shipping_id
    assert checkout.shipping_method_name == app_shipping_name

    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assert checkout.assigned_delivery.id == assigned_delivery.id

    assigned_delivery.refresh_from_db()
    assert assigned_delivery.name == app_shipping_name
    assert assigned_delivery.external_shipping_method_id == app_shipping_id
    assert assigned_delivery.built_in_shipping_method_id is None
    assert assigned_delivery.price_amount == Decimal(0)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_external_shipping_to_checkout_with_the_same_shipping_method(
    checkout_with_item, shipping_method, settings
):
    # given
    app_shipping_id = "abcd"
    app_shipping_name = "Shipping"
    external_shipping_data = ShippingMethodData(
        name=app_shipping_name, id=app_shipping_id, price=Money(0, "USD")
    )
    checkout = checkout_with_item
    checkout.external_shipping_method_id = app_shipping_id
    checkout.shipping_method_name = app_shipping_name
    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout_with_item,
        name=app_shipping_name,
        price_amount=0,
        currency=checkout_with_item.currency,
        external_shipping_method_id=checkout.external_shipping_method_id,
    )
    checkout_with_item.assigned_delivery = assigned_delivery
    checkout_with_item.save()

    # when
    fields_to_updated = assign_external_shipping_to_checkout(
        checkout, external_shipping_data
    )

    # then
    assert not fields_to_updated
    assert (
        PRIVATE_META_APP_SHIPPING_ID not in checkout.metadata_storage.private_metadata
    )
    assert checkout.external_shipping_method_id == app_shipping_id
    assert checkout.shipping_method_name == app_shipping_name
    assert checkout.shipping_methods_stale_at is None

    assigned_delivery.refresh_from_db()
    assert assigned_delivery.name == app_shipping_name
    assert assigned_delivery.external_shipping_method_id == app_shipping_id
    assert assigned_delivery.built_in_shipping_method_id is None
    assert assigned_delivery.price_amount == Decimal(0)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_built_in_shipping_to_checkout_without_delivery_method(
    checkout, shipping_method, settings
):
    # given
    expected_updated_fields = {
        "shipping_method_id",
        "shipping_method_name",
        "undiscounted_base_shipping_price_amount",
        "shipping_methods_stale_at",
    }
    shipping_method_data = ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        price=Money(10, checkout.currency),
    )
    # when
    fields_to_update = assign_built_in_shipping_to_checkout(
        checkout, shipping_method_data
    )

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.shipping_method == shipping_method
    assert checkout.shipping_method_name == shipping_method.name
    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assigned_delivery = checkout.assigned_delivery
    assert assigned_delivery.name == shipping_method.name
    assert assigned_delivery.external_shipping_method_id is None
    assert assigned_delivery.built_in_shipping_method_id == shipping_method.id
    assert assigned_delivery.price_amount == Decimal(10)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_built_in_shipping_to_checkout_with_cc(
    checkout_with_delivery_method_for_cc, shipping_method, settings
):
    # given
    checkout = checkout_with_delivery_method_for_cc
    expected_updated_fields = {
        "shipping_method_id",
        "shipping_method_name",
        "collection_point_id",
        "shipping_address_id",
        "undiscounted_base_shipping_price_amount",
        "save_shipping_address",
        "shipping_methods_stale_at",
    }
    shipping_method_data = ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        price=Money(10, checkout.currency),
    )

    # when
    fields_to_update = assign_built_in_shipping_to_checkout(
        checkout, shipping_method_data
    )
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.shipping_method == shipping_method
    assert checkout.shipping_method_name == shipping_method.name
    assert checkout.collection_point_id is None
    assert checkout.shipping_address_id is None
    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assigned_delivery = checkout.assigned_delivery
    assert assigned_delivery.name == shipping_method.name
    assert assigned_delivery.external_shipping_method_id is None
    assert assigned_delivery.built_in_shipping_method_id == shipping_method.id
    assert assigned_delivery.price_amount == Decimal(10)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_built_in_shipping_to_checkout_with_external_shipping_method(
    checkout, shipping_method, settings
):
    # given
    checkout.external_shipping_method_id = "ext-id"
    checkout.shipping_method_name = "Ext default"
    expected_updated_fields = {
        "shipping_method_id",
        "shipping_method_name",
        "external_shipping_method_id",
        "undiscounted_base_shipping_price_amount",
        "shipping_methods_stale_at",
    }
    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        name=checkout.shipping_method_name,
        external_shipping_method_id=checkout.external_shipping_method_id,
        price_amount=0,
        currency=checkout.currency,
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    shipping_method_data = ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        price=Money(10, checkout.currency),
    )

    # when
    fields_to_update = assign_built_in_shipping_to_checkout(
        checkout, shipping_method_data
    )
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.shipping_method == shipping_method
    assert checkout.shipping_method_name == shipping_method.name
    assert checkout.external_shipping_method_id is None

    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assigned_delivery = CheckoutDelivery.objects.get()
    assert assigned_delivery.name == shipping_method.name
    assert assigned_delivery.external_shipping_method_id is None
    assert assigned_delivery.built_in_shipping_method_id == shipping_method.id
    assert assigned_delivery.price_amount == Decimal(10)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_built_in_shipping_to_checkout_with_different_shipping_method(
    checkout, shipping_method, shipping_method_weight_based, settings
):
    # given
    checkout.shipping_method = shipping_method_weight_based
    checkout.shipping_method_name = shipping_method_weight_based.name

    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        name=shipping_method_weight_based.name,
        built_in_shipping_method_id=shipping_method_weight_based.id,
        external_shipping_method_id=None,
        price_amount=0,
        currency=checkout.currency,
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    shipping_method_data = ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        price=Money(10, checkout.currency),
    )

    expected_updated_fields = {
        "shipping_method_id",
        "shipping_method_name",
        "undiscounted_base_shipping_price_amount",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_update = assign_built_in_shipping_to_checkout(
        checkout, shipping_method_data
    )

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.shipping_method == shipping_method
    assert checkout.shipping_method_name == shipping_method.name

    assert (
        checkout.shipping_methods_stale_at
        == timezone.now() + settings.CHECKOUT_SHIPPING_OPTIONS_TTL
    )

    assigned_delivery = CheckoutDelivery.objects.get()
    assert assigned_delivery.name == shipping_method.name
    assert assigned_delivery.external_shipping_method_id is None
    assert assigned_delivery.built_in_shipping_method_id == shipping_method.id
    assert assigned_delivery.price_amount == Decimal(10)
    assert assigned_delivery.currency == "USD"


@freeze_time("2023-01-01 12:00:00")
def test_assign_built_in_shipping_to_checkout_with_the_same_shipping_method(
    checkout, shipping_method
):
    # given
    shipping_price_amount = Decimal(10)
    checkout.shipping_method = shipping_method
    checkout.shipping_method_name = shipping_method.name
    checkout.undiscounted_base_shipping_price_amount = shipping_price_amount
    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        name=shipping_method.name,
        price_amount=0,
        currency=checkout.currency,
        built_in_shipping_method_id=shipping_method.id,
        external_shipping_method_id=None,
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    shipping_method_data = ShippingMethodData(
        id=str(shipping_method.id),
        name=shipping_method.name,
        price=Money(shipping_price_amount, checkout.currency),
    )

    # when
    fields_to_update = assign_built_in_shipping_to_checkout(
        checkout, shipping_method_data
    )

    # then
    assert not fields_to_update
    assert checkout.shipping_method == shipping_method
    assert checkout.shipping_method_name == shipping_method.name

    assigned_delivery.refresh_from_db()
    assert assigned_delivery.name == shipping_method.name
    assert assigned_delivery.external_shipping_method_id is None
    assert assigned_delivery.built_in_shipping_method_id == shipping_method.id
    assert assigned_delivery.price_amount == Decimal(0)
    assert assigned_delivery.currency == "USD"


def test_assign_collection_point_to_checkout_without_delivery_method(
    checkout, warehouses_for_cc
):
    # given
    collection_point = warehouses_for_cc[0]
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert expected_updated_fields == set(fields_to_update)

    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.assigned_delivery is None


def test_assign_collection_point_to_checkout_with_external_shipping_method(
    checkout, warehouses_for_cc
):
    # given
    checkout.external_shipping_method_id = "ext-id"
    checkout.shipping_method_name = "Ext default"
    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        name=checkout.shipping_method_name,
        price_amount=0,
        currency=checkout.currency,
        external_shipping_method_id=checkout.external_shipping_method_id,
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    collection_point = warehouses_for_cc[0]
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "external_shipping_method_id",
        "shipping_method_name",
        "save_shipping_address",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.external_shipping_method_id is None
    assert checkout.shipping_method_name is None
    assert checkout.shipping_methods_stale_at is None
    assert checkout.assigned_delivery is None
    assert CheckoutDelivery.objects.count() == 0


def test_assign_collection_point_to_checkout_with_shipping_method(
    checkout, shipping_method_weight_based, warehouses_for_cc
):
    # given
    checkout.shipping_method = shipping_method_weight_based
    checkout.shipping_method_name = shipping_method_weight_based.name
    assigned_delivery = CheckoutDelivery.objects.create(
        checkout=checkout,
        name=shipping_method_weight_based.name,
        price_amount=0,
        currency=checkout.currency,
        built_in_shipping_method_id=shipping_method_weight_based.id,
        external_shipping_method_id=None,
    )
    checkout.assigned_delivery = assigned_delivery
    checkout.save()

    collection_point = warehouses_for_cc[0]
    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "shipping_method_id",
        "shipping_method_name",
        "save_shipping_address",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.shipping_method_id is None
    assert checkout.shipping_method_name is None

    assert checkout.shipping_methods_stale_at is None
    assert checkout.assigned_delivery is None
    assert CheckoutDelivery.objects.count() == 0


def test_assign_collection_point_to_checkout_with_different_cc(
    checkout, warehouses_for_cc, address_other_country
):
    # given
    previous_collection_point = warehouses_for_cc[1]
    previous_collection_point.address = address_other_country

    new_collection_point = warehouses_for_cc[0]

    checkout.collection_point = previous_collection_point
    checkout.shipping_address = previous_collection_point.address

    expected_updated_fields = {
        "collection_point_id",
        "shipping_address_id",
        "save_shipping_address",
        "shipping_methods_stale_at",
    }

    # when
    fields_to_update = assign_collection_point_to_checkout(
        checkout, new_collection_point
    )

    # then
    assert expected_updated_fields == set(fields_to_update)
    assert checkout.collection_point == new_collection_point
    assert checkout.shipping_address == new_collection_point.address
    assert int(checkout.shipping_address_id) != int(new_collection_point.address.id)
    assert checkout.assigned_delivery is None


def test_assign_collection_point_to_checkout_with_the_same_cc(
    checkout, warehouses_for_cc, address_other_country
):
    # given
    collection_point = warehouses_for_cc[0]

    checkout.collection_point = collection_point
    checkout.shipping_address = collection_point.address.get_copy()

    # when
    fields_to_update = assign_collection_point_to_checkout(checkout, collection_point)

    # then
    assert not fields_to_update
    assert checkout.collection_point == collection_point
    assert checkout.shipping_address == collection_point.address
    assert int(checkout.shipping_address_id) != int(collection_point.address.id)
    assert checkout.assigned_delivery is None


def test_get_external_shipping_id_from_metadata(checkout):
    # given
    app_shipping_id = "abcd"
    initial_private_metadata = {PRIVATE_META_APP_SHIPPING_ID: app_shipping_id}
    checkout.metadata_storage.private_metadata = initial_private_metadata
    checkout.metadata_storage.save()

    # when
    shipping_id = get_external_shipping_id(checkout)

    # then
    assert shipping_id == app_shipping_id


def test_get_external_shipping_id(checkout):
    # given
    app_shipping_id = "abcd"
    checkout.external_shipping_method_id = app_shipping_id

    # when
    shipping_id = get_external_shipping_id(checkout)

    # then
    assert shipping_id == app_shipping_id


def test_remove_external_shipping_from_checkout(checkout):
    # given
    app_shipping_id = "abcd"
    expected_private_metadata = {"test": "123"}
    initial_private_metadata = {PRIVATE_META_APP_SHIPPING_ID: app_shipping_id}
    checkout.external_shipping_method_id = app_shipping_id

    initial_private_metadata.update(expected_private_metadata)
    checkout.metadata_storage.private_metadata = initial_private_metadata
    checkout.metadata_storage.save()

    # when
    remove_external_shipping_from_checkout(checkout)

    # then
    assert checkout.metadata_storage.private_metadata == expected_private_metadata
    assert checkout.external_shipping_method_id is None
    assert checkout.shipping_method_name is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)


def test_remove_external_shipping_from_checkout_with_save(checkout):
    # given
    app_shipping_id = "abcd"
    expected_private_metadata = {"test": "123"}
    initial_private_metadata = {PRIVATE_META_APP_SHIPPING_ID: app_shipping_id}
    checkout.external_shipping_method_id = app_shipping_id

    initial_private_metadata.update(expected_private_metadata)
    checkout.metadata_storage.private_metadata = initial_private_metadata
    checkout.metadata_storage.save()

    # when
    remove_external_shipping_from_checkout(checkout, save=True)

    # then
    checkout.refresh_from_db()
    assert checkout.metadata_storage.private_metadata == expected_private_metadata
    assert checkout.external_shipping_method_id is None
    assert checkout.shipping_method_name is None
    assert checkout.undiscounted_base_shipping_price_amount == Decimal(0)
