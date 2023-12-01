import warnings
from datetime import timedelta

import graphene
import pytest
from django.utils import timezone
from django_countries import countries

from ....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....shipping.models import ShippingZone
from ....warehouse import WarehouseClickAndCollectOption
from ....warehouse.models import PreorderReservation, Reservation, Stock, Warehouse
from ...tests.utils import get_graphql_content

COUNTRY_CODE = "US"

QUERY_QUANTITY_AVAILABLE = """
    query variantAvailability($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            quantityAvailable
        }
    }
    """


def test_variant_quantity_available_without_country_code(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7


def test_variant_quantity_available_without_country_code_or_channel(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk)
    }
    with warnings.catch_warnings(record=True) as warns:
        response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 7
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )


def test_variant_quantity_available_without_country_code_stock_only_in_cc_warehouse(
    api_client, variant, channel_USD, warehouse_for_cc
):
    # given
    quantity = 4
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == quantity


def test_variant_quantity_available_without_country_code_local_cc_warehouse(
    api_client, variant, channel_USD, warehouse_for_cc, warehouse
):
    # given
    quantity_cc = 7
    # stock for collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )

    quantity = 5
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == quantity_cc


def test_variant_quantity_available_without_country_code_global_cc_warehouse(
    api_client, variant, channel_USD, warehouse_for_cc, warehouse
):
    # given
    quantity_cc = 4

    warehouse_for_cc.click_and_collect_option = (
        WarehouseClickAndCollectOption.ALL_WAREHOUSES
    )
    warehouse_for_cc.save(update_fields=["click_and_collect_option"])

    # stock for collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )

    quantity = 5
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == quantity + quantity_cc


def test_variant_quantity_available_when_one_stock_is_exceeded(
    api_client, variant_with_many_stocks, channel_USD
):
    # make first stock exceeded
    stock = variant_with_many_stocks.stocks.first()
    stock.quantity = -99
    stock.save()

    stock_2 = variant_with_many_stocks.stocks.last()

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == max(
        0, stock.quantity + stock_2.quantity
    )


def test_variant_quantity_available_without_country_code_and_no_channel_shipping_zones(
    api_client, variant_with_many_stocks, channel_USD
):
    channel_USD.shipping_zones.clear()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 0


def test_variant_quantity_available_no_country_warehouse_without_zone(
    api_client, variant_with_many_stocks, channel_USD, channel_PLN
):
    """Test that available quantity only includes warehouses that belong to a shipping zone.

    In this case, a channel is provided, but no country code.
    """
    # given
    assert variant_with_many_stocks.stocks.count() == 2

    stock_1, stock_2 = variant_with_many_stocks.stocks.all()
    # clear shipping zones one of variant warehouses
    stock_2.warehouse.shipping_zones.clear()

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == stock_1.quantity


def test_variant_quantity_available_no_channel_and_no_country_warehouse_without_zone(
    staff_api_client,
    variant_with_many_stocks,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_discounts,
    permission_manage_orders,
):
    """Test that available quantity only includes warehouses that belong to a shipping zone.

    In this case, neither a channel nor country code is provided.
    """
    # given
    assert variant_with_many_stocks.stocks.count() == 2

    stock_1, stock_2 = variant_with_many_stocks.stocks.all()
    # clear shipping zones one of variant warehouses
    stock_2.warehouse.shipping_zones.clear()

    staff_api_client.user.user_permissions.add(
        permission_manage_products,
        permission_manage_discounts,
        permission_manage_orders,
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk)
    }

    # when
    response = staff_api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == stock_1.quantity


def test_variant_quantity_available_only_warehouse_without_zone_no_channel_no_country(
    staff_api_client,
    variant,
    stock,
    channel_USD,
    channel_PLN,
    permission_manage_products,
    permission_manage_discounts,
    permission_manage_orders,
):
    """Test that availability is 0 if no warehouses belong to a shipping zone."""
    # given
    assert variant.stocks.count() == 1
    # clear shipping zones for variant warehouses
    stock.warehouse.shipping_zones.clear()

    staff_api_client.user.user_permissions.add(
        permission_manage_products,
        permission_manage_discounts,
        permission_manage_orders,
    )

    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_QUANTITY_AVAILABLE, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["quantityAvailable"] == 0


QUERY_VARIANT_AVAILABILITY = """
    query variantAvailability(
        $id: ID!, $country: CountryCode, $address: AddressInput, $channel: String
    ) {
        productVariant(id: $id, channel: $channel) {
            deprecatedByCountry: quantityAvailable(countryCode: $country)
            byAddress: quantityAvailable(address: $address)
        }
    }
"""


def test_variant_quantity_available_with_country_code(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_country_code_warehouse_in_many_shipping_zones(
    api_client, variant_with_many_stocks, channel_USD, shipping_zone_JPY
):
    shipping_zone = ShippingZone.objects.create(
        name="Test",
        countries=[code for code, name in countries],
    )
    shipping_zone.channels.add(channel_USD)
    warehouse = Warehouse.objects.get(slug="warehouse2")
    warehouse.shipping_zones.add(shipping_zone)
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_country_code_no_channel_shipping_zones(
    api_client, variant_with_many_stocks, channel_USD
):
    channel_USD.shipping_zones.clear()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 0
    assert variant_data["byAddress"] == 0


def test_variant_quantity_available_with_country_code_only_one_available_warehouse(
    api_client, variant_with_many_stocks, channel_USD, warehouses_with_shipping_zone
):
    shipping_zone = ShippingZone.objects.create(
        name="Test", countries=[code for code, name in countries]
    )
    warehouses_with_shipping_zone[0].shipping_zones.set([shipping_zone])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "address": {"country": COUNTRY_CODE},
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 3
    assert variant_data["byAddress"] == 3


def test_variant_quantity_available_with_null_as_country_code(
    api_client, variant_with_many_stocks, channel_USD
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": None,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_country_code_only_negative_quantity(
    api_client,
    variant,
    channel_USD,
    warehouse_for_cc,
    warehouse,
):
    """Test that click-and-collect warehouse quantities are ignored when not part of the shipping zone.

    In this case, the non-C&C warehouse has negative quantity.
    """
    # given
    quantity_cc = 7
    # stock for local collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )

    quantity = -5
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "address": {"country": COUNTRY_CODE},
        "country": COUNTRY_CODE,
    }

    # when
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["byAddress"] == 0
    assert variant_data["deprecatedByCountry"] == 0


def test_variant_quantity_available_with_country_code_and_cc_warehouse_without_zone(
    api_client,
    variant,
    channel_USD,
    warehouse_for_cc,
    warehouse,
):
    """Test that click-and-collect warehouse quantities are ignored when not part of the shipping zone.

    In this case, both quantities are positive.
    """
    # given
    quantity_cc = 7
    # stock for local collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )

    quantity = 5
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "address": {"country": COUNTRY_CODE},
        "country": COUNTRY_CODE,
    }

    # when
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["byAddress"] == quantity
    assert variant_data["deprecatedByCountry"] == quantity


def test_variant_quantity_available_with_country_code_and_local_cc_warehouse_with_zone(
    api_client, variant, channel_USD, warehouse_for_cc, warehouse, shipping_zone
):
    """Test that availability includes click-and-collect warehouse that belongs to the shipping zone.

    In this case, both quantities are positive.
    """
    # given
    quantity_cc = 7
    # stock for local collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )
    warehouse_for_cc.shipping_zones.add(shipping_zone)

    quantity = 5
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "address": {"country": COUNTRY_CODE},
        "country": COUNTRY_CODE,
    }

    # when
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["byAddress"] == quantity_cc + quantity
    assert variant_data["deprecatedByCountry"] == quantity + quantity_cc


def test_variant_qty_available_with_country_code_and_local_cc_warehouse_negative_qty(
    api_client, variant, channel_USD, warehouse_for_cc, warehouse, shipping_zone
):
    """Test that availability includes click-and-collect warehouse that belongs to the shipping zone.

    In this case, the non-C&C warehouse has negative quantity.
    """
    # given
    quantity_cc = 7
    # stock for local collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )
    warehouse_for_cc.shipping_zones.add(shipping_zone)

    quantity = -1
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "address": {"country": COUNTRY_CODE},
        "country": COUNTRY_CODE,
    }

    # when
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["byAddress"] == quantity_cc + quantity
    assert variant_data["deprecatedByCountry"] == quantity + quantity_cc


def test_variant_quantity_available_with_country_code_and_global_cc_warehouse(
    api_client, variant, channel_USD, warehouse_for_cc, shipping_zone, warehouse
):
    # given
    quantity_cc = 7
    # stock for local collection point warehouse
    Stock.objects.create(
        warehouse=warehouse_for_cc, product_variant=variant, quantity=quantity_cc
    )
    warehouse_for_cc.shipping_zones.add(shipping_zone)

    quantity = 5
    # stock for standard warehouse
    Stock.objects.create(
        warehouse=warehouse, product_variant=variant, quantity=quantity
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "channel": channel_USD.slug,
        "address": {"country": COUNTRY_CODE},
        "country": COUNTRY_CODE,
    }

    # when
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)

    # then
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["byAddress"] == quantity + quantity_cc
    assert variant_data["deprecatedByCountry"] == quantity + quantity_cc


def test_variant_quantity_available_with_max(
    api_client, variant_with_many_stocks, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    stock = variant_with_many_stocks.stocks.first()
    stock.quantity = 16
    stock.save(update_fields=["quantity"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_quantity_available_without_stocks(
    api_client, variant_with_many_stocks, channel_USD
):
    variant_with_many_stocks.stocks.all().delete()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 0
    assert variant_data["byAddress"] == 0


def test_variant_quantity_available_with_allocations(
    api_client,
    variant_with_many_stocks,
    order_line_with_allocation_in_many_stocks,
    order_line_with_one_allocation,
    channel_USD,
):
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 3
    assert variant_data["byAddress"] == 3


def test_variant_quantity_available_with_enabled_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reservation_in_many_stocks,
    channel_USD,
):
    variant = checkout_line_with_reservation_in_many_stocks.variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 4
    assert variant_data["byAddress"] == 4


def test_variant_quantity_available_with_enabled_expired_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reservation_in_many_stocks,
    channel_USD,
):
    Reservation.objects.update(reserved_until=timezone.now() - timedelta(minutes=2))
    variant = checkout_line_with_reservation_in_many_stocks.variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_with_disabled_reservations(
    api_client,
    checkout_line_with_reservation_in_many_stocks,
    channel_USD,
):
    variant = checkout_line_with_reservation_in_many_stocks.variant
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == 7
    assert variant_data["byAddress"] == 7


def test_variant_quantity_available_without_inventory_tracking(
    api_client, variant_with_many_stocks, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant_with_many_stocks.track_inventory = False
    variant_with_many_stocks.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_quantity_available_without_inventory_tracking_no_global_limit(
    api_client, variant_with_many_stocks, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = None
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant_with_many_stocks.track_inventory = False
    variant_with_many_stocks.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant_with_many_stocks.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] is None
    assert variant_data["byAddress"] is None


def test_variant_quantity_available_without_inventory_tracking_and_stocks(
    api_client, variant, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant.track_inventory = False
    variant.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_qty_available_without_inventory_tracking_and_stocks_no_global_limit(
    api_client, variant, site_settings, channel_USD
):
    site_settings.limit_quantity_per_checkout = None
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant.track_inventory = False
    variant.save(update_fields=["track_inventory"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] is None
    assert variant_data["byAddress"] is None


@pytest.mark.parametrize("global_limit", [15, None])
def test_variant_quantity_available_preorder_with_channel_threshold(
    api_client,
    site_settings,
    preorder_variant_channel_threshold,
    channel_USD,
    global_limit,
):
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_channel_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    channel_listing = variant.channel_listings.get()
    assert (
        variant_data["deprecatedByCountry"]
        == channel_listing.preorder_quantity_threshold
    )
    assert variant_data["byAddress"] == channel_listing.preorder_quantity_threshold


def test_variant_quantity_available_preorder_without_reservations(
    site_settings_with_reservations,
    api_client,
    preorder_variant_channel_threshold,
    channel_USD,
):
    site_settings_with_reservations.limit_quantity_per_checkout = 15
    site_settings_with_reservations.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_channel_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    channel_listing = variant.channel_listings.get()
    assert (
        variant_data["deprecatedByCountry"]
        == channel_listing.preorder_quantity_threshold
    )
    assert variant_data["byAddress"] == channel_listing.preorder_quantity_threshold


def test_variant_quantity_available_preorder_with_channel_threshold_and_reservation(
    site_settings_with_reservations,
    api_client,
    preorder_variant_channel_threshold,
    checkout_line_with_reserved_preorder_item,
    channel_USD,
):
    site_settings_with_reservations.limit_quantity_per_checkout = 15
    site_settings_with_reservations.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_channel_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    channel_listing = variant.channel_listings.get()

    reservation = PreorderReservation.objects.all().first()
    available_quantity = channel_listing.preorder_quantity_threshold
    available_quantity -= reservation.quantity_reserved

    assert variant_data["deprecatedByCountry"] == available_quantity
    assert variant_data["byAddress"] == available_quantity


@pytest.mark.parametrize("global_limit", [15, None])
def test_variant_quantity_available_preorder_with_global_threshold(
    api_client,
    site_settings,
    preorder_variant_global_threshold,
    channel_USD,
    global_limit,
):
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant = preorder_variant_global_threshold
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == variant.preorder_global_threshold
    assert variant_data["byAddress"] == variant.preorder_global_threshold


def test_variant_quantity_available_preorder_with_global_threshold_and_reservations(
    site_settings_with_reservations,
    api_client,
    checkout_line_with_reserved_preorder_item,
    channel_USD,
):
    site_settings_with_reservations.limit_quantity_per_checkout = 15
    site_settings_with_reservations.save(update_fields=["limit_quantity_per_checkout"])

    variant = checkout_line_with_reserved_preorder_item.variant
    variant.channel_listings.update(preorder_quantity_threshold=None)
    variant.preorder_global_threshold = 10
    variant.save()

    reservation = PreorderReservation.objects.all().first()
    available_quantity = (
        variant.preorder_global_threshold - reservation.quantity_reserved
    )

    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]
    assert variant_data["deprecatedByCountry"] == available_quantity
    assert variant_data["byAddress"] == available_quantity


@pytest.mark.parametrize("global_limit", [15, None])
def test_variant_quantity_available_preorder_without_threshold(
    api_client,
    preorder_variant_global_threshold,
    site_settings,
    channel_USD,
    global_limit,
):
    site_settings.limit_quantity_per_checkout = global_limit
    site_settings.save(update_fields=["limit_quantity_per_checkout"])

    variant = preorder_variant_global_threshold
    variant.preorder_global_threshold = None
    variant.save(update_fields=["preorder_global_threshold"])
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    variant_data = content["data"]["productVariant"]

    assert (
        variant_data["deprecatedByCountry"] == site_settings.limit_quantity_per_checkout
    )
    assert variant_data["byAddress"] == site_settings.limit_quantity_per_checkout


def test_variant_quantity_available_preorder_without_channel(
    api_client,
    site_settings,
    preorder_variant_global_threshold,
    channel_USD,
):
    site_settings.limit_quantity_per_checkout = 15
    site_settings.save(update_fields=["limit_quantity_per_checkout"])
    variant = preorder_variant_global_threshold
    variant.channel_listings.all().delete()
    variables = {
        "id": graphene.Node.to_global_id("ProductVariant", variant.pk),
        "country": COUNTRY_CODE,
        "channel": channel_USD.slug,
    }
    response = api_client.post_graphql(QUERY_VARIANT_AVAILABILITY, variables)
    content = get_graphql_content(response)
    assert not content["data"]["productVariant"]
