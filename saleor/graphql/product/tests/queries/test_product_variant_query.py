from decimal import Decimal

import graphene
import pytest
from django.contrib.sites.models import Site
from measurement.measures import Weight

from .....attribute.utils import associate_attribute_values_to_instance
from .....core.units import WeightUnits
from .....warehouse import WarehouseClickAndCollectOption
from ....core.enums import WeightUnitsEnum
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_VARIANT = """query ProductVariantDetails(
        $id: ID!, $address: AddressInput, $countryCode: CountryCode, $channel: String
    ) {
        productVariant(id: $id, channel: $channel) {
            id
            deprecatedStocksByCountry: stocks(countryCode: $countryCode) {
                id
            }
            stocksByAddress: stocks(address: $address) {
                id
            }
            attributes {
                attribute {
                    id
                    name
                    slug
                    choices(first: 10) {
                        edges {
                            node {
                                id
                                name
                                slug
                            }
                        }
                    }
                }
                values {
                    id
                    name
                    slug
                }
            }
            media {
                id
            }
            name
            channelListings {
                channel {
                    slug
                }
                price {
                    currency
                    amount
                }
                costPrice {
                    currency
                    amount
                }
            }
            product {
                id
            }
            weight {
                unit
                value
            }
            created
        }
    }
"""


def test_fetch_variant(
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    settings,
    channel_USD,
):
    # given
    query = QUERY_VARIANT
    variant = product.variants.first()
    variant.weight = Weight(kg=10)
    variant.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.G
    site_settings.save(update_fields=["default_weight_unit"])
    Site.objects.clear_cache()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countryCode": "EU", "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert data["created"] == variant.created_at.isoformat()

    stocks_count = variant.stocks.count()
    assert len(data["deprecatedStocksByCountry"]) == stocks_count
    assert len(data["stocksByAddress"]) == stocks_count

    assert data["weight"]["value"] == 10000
    assert data["weight"]["unit"] == WeightUnitsEnum.G.name
    channel_listing_data = data["channelListings"][0]
    channel_listing = variant.channel_listings.get()
    assert channel_listing_data["channel"]["slug"] == channel_listing.channel.slug
    assert channel_listing_data["price"]["currency"] == channel_listing.currency
    assert channel_listing_data["price"]["amount"] == channel_listing.price_amount
    assert channel_listing_data["costPrice"]["currency"] == channel_listing.currency
    assert (
        channel_listing_data["costPrice"]["amount"] == channel_listing.cost_price_amount
    )


def test_fetch_variant_no_stocks(
    staff_api_client,
    product,
    permission_manage_products,
    site_settings,
    channel_USD,
):
    # given
    query = QUERY_VARIANT
    variant = product.variants.first()
    variant.weight = Weight(kg=10)
    variant.save(update_fields=["weight"])

    site_settings.default_weight_unit = WeightUnits.G
    site_settings.save(update_fields=["default_weight_unit"])
    Site.objects.clear_cache()

    warehouse = variant.stocks.first().warehouse
    # remove the warehouse channels
    # the stocks for this warehouse shouldn't be returned
    warehouse.channels.clear()

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countryCode": "EU", "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert data["created"] == variant.created_at.isoformat()

    assert not data["deprecatedStocksByCountry"]
    assert not data["stocksByAddress"]

    assert data["weight"]["value"] == 10000
    assert data["weight"]["unit"] == WeightUnitsEnum.G.name
    channel_listing_data = data["channelListings"][0]
    channel_listing = variant.channel_listings.get()
    assert channel_listing_data["channel"]["slug"] == channel_listing.channel.slug
    assert channel_listing_data["price"]["currency"] == channel_listing.currency
    assert channel_listing_data["price"]["amount"] == channel_listing.price_amount
    assert channel_listing_data["costPrice"]["currency"] == channel_listing.currency
    assert (
        channel_listing_data["costPrice"]["amount"] == channel_listing.cost_price_amount
    )


def test_fetch_variant_stocks_from_click_and_collect_warehouse(
    staff_api_client,
    product,
    permission_manage_products,
    channel_USD,
):
    # given
    query = QUERY_VARIANT
    variant = product.variants.first()
    stocks_count = variant.stocks.count()
    warehouse = variant.stocks.first().warehouse

    # remove the warehouse shipping zones and mark it as click and collect
    # the stocks for this warehouse should be still returned
    warehouse.shipping_zones.clear()
    warehouse.click_and_collect_option = WarehouseClickAndCollectOption.LOCAL_STOCK
    warehouse.save(update_fields=["click_and_collect_option"])

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "countryCode": "EU", "channel": channel_USD.slug}
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = staff_api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariant"]
    assert data["name"] == variant.name
    assert data["created"] == variant.created_at.isoformat()

    assert len(data["stocksByAddress"]) == stocks_count
    assert not data["deprecatedStocksByCountry"]


QUERY_PRODUCT_VARIANT_CHANNEL_LISTING = """
    query ProductVariantDetails($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            id
            channelListings {
                channel {
                    slug
                }
                price {
                    currency
                    amount
                }
                costPrice {
                    currency
                    amount
                }
            }
        }
    }
"""


def test_get_product_variant_channel_listing_as_staff_user(
    staff_api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]
    channel_listings = variant.channel_listings.all()
    for channel_listing in channel_listings:
        assert {
            "channel": {"slug": channel_listing.channel.slug},
            "price": {
                "currency": channel_listing.currency,
                "amount": channel_listing.price_amount,
            },
            "costPrice": {
                "currency": channel_listing.currency,
                "amount": channel_listing.cost_price_amount,
            },
        } in data["channelListings"]
    assert len(data["channelListings"]) == variant.channel_listings.count()


def test_get_product_variant_channel_listing_as_app(
    app_api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = app_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]
    channel_listings = variant.channel_listings.all()
    for channel_listing in channel_listings:
        assert {
            "channel": {"slug": channel_listing.channel.slug},
            "price": {
                "currency": channel_listing.currency,
                "amount": channel_listing.price_amount,
            },
            "costPrice": {
                "currency": channel_listing.currency,
                "amount": channel_listing.cost_price_amount,
            },
        } in data["channelListings"]
    assert len(data["channelListings"]) == variant.channel_listings.count()


def test_get_product_variant_channel_listing_as_customer(
    user_api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )

    # then
    assert_no_permission(response)


def test_get_product_variant_channel_listing_as_anonymous(
    api_client,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_CHANNEL_LISTING,
        variables,
    )

    # then
    assert_no_permission(response)


QUERY_PRODUCT_VARIANT_STOCKS = """
  fragment Stock on Stock {
    id
    quantity
    warehouse {
      slug
    }
  }
  query ProductVariantDetails(
    $id: ID!
    $channel: String
    $address: AddressInput
  ) {
    productVariant(id: $id, channel: $channel) {
      id
      stocksNoAddress: stocks {
        ...Stock
      }
      stocksWithAddress: stocks(address: $address) {
        ...Stock
      }
    }
  }
"""


def test_get_product_variant_stocks(
    staff_api_client,
    variant_with_many_stocks_different_shipping_zones,
    channel_USD,
    permission_manage_products,
):
    # given
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_STOCKS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    all_stocks = variant.stocks.all()
    pl_stocks = variant.stocks.filter(
        warehouse__shipping_zones__countries__contains="PL"
    )
    data = content["data"]["productVariant"]

    # When no address is provided, it should return all stocks of the variant available
    # in given channel.
    assert len(data["stocksNoAddress"]) == all_stocks.count()
    no_address_stocks_ids = [stock["id"] for stock in data["stocksNoAddress"]]
    assert all(
        graphene.Node.to_global_id("Stock", stock.pk) in no_address_stocks_ids
        for stock in all_stocks
    )

    # When address is given, return only stocks from warehouse that ship to that
    # address.
    assert len(data["stocksWithAddress"]) == pl_stocks.count()
    with_address_stocks_ids = [stock["id"] for stock in data["stocksWithAddress"]]
    assert all(
        graphene.Node.to_global_id("Stock", stock.pk) in with_address_stocks_ids
        for stock in pl_stocks
    )


def test_get_product_variant_stocks_no_channel_shipping_zones(
    staff_api_client,
    variant_with_many_stocks_different_shipping_zones,
    channel_USD,
    permission_manage_products,
):
    # given
    channel_USD.shipping_zones.clear()
    variant = variant_with_many_stocks_different_shipping_zones
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "address": {"country": "PL"},
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_STOCKS,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    stocks_count = variant.stocks.count()
    data = content["data"]["productVariant"]
    assert data["stocksNoAddress"] == []
    assert data["stocksWithAddress"] == []
    assert stocks_count > 0


def _fetch_variant(client, variant, channel_slug=None, permissions=None):
    query = """
    query ProductVariantDetails($variantId: ID!, $channel: String) {
        productVariant(id: $variantId, channel: $channel) {
            id
            product {
                id
            }
        }
    }
    """
    variables = {"variantId": graphene.Node.to_global_id("ProductVariant", variant.id)}
    if channel_slug:
        variables["channel"] = channel_slug
    response = client.post_graphql(
        query, variables, permissions=permissions, check_no_permissions=False
    )
    content = get_graphql_content(response)
    return content["data"]["productVariant"]


def test_fetch_unpublished_variant_staff_user(
    staff_api_client, unavailable_product_with_variant, permission_manage_products
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(
        staff_api_client,
        variant,
        permissions=[permission_manage_products],
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id(
        "Product", unavailable_product_with_variant.pk
    )

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_unpublished_variant_customer(
    user_api_client, unavailable_product_with_variant, channel_USD
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(user_api_client, variant, channel_slug=channel_USD.slug)
    assert data is None


def test_fetch_unpublished_variant_anonymous_user(
    api_client, unavailable_product_with_variant, channel_USD
):
    variant = unavailable_product_with_variant.variants.first()
    data = _fetch_variant(api_client, variant, channel_slug=channel_USD.slug)
    assert data is None


def test_fetch_variant_without_sku_staff_user(
    staff_api_client, product, variant, permission_manage_products
):
    variant.sku = None
    variant.save()

    data = _fetch_variant(
        staff_api_client,
        variant,
        permissions=[permission_manage_products],
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_variant_without_sku_customer(
    user_api_client, product, variant, channel_USD
):
    variant.sku = None
    variant.save()

    data = _fetch_variant(
        user_api_client,
        variant,
        channel_slug=channel_USD.slug,
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


def test_fetch_variant_without_sku_anonymous(api_client, product, variant, channel_USD):
    variant.sku = None
    variant.save()

    data = _fetch_variant(
        api_client,
        variant,
        channel_slug=channel_USD.slug,
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    assert data["id"] == variant_id
    assert data["product"]["id"] == product_id


QUERY_PRODUCT_VARIANT_IN_FEDERATION = """
query GetProductVariantInFederation($representations: [_Any!]!) {
  _entities(representations: $representations) {
    __typename
    ... on ProductVariant {
      id
      name
    }
  }
}
"""


def test_query_product_variant_for_federation_as_customer(
    api_client, variant, channel_USD
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": channel_USD.slug,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductVariant",
            "id": variant_id,
            "name": variant.name,
        }
    ]


def test_query_product_variant_for_federation_as_customer_not_existing_channel(
    api_client, variant
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": "not-existing-channel",
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_variant_for_federation_as_customer_channel_not_active(
    api_client, variant, channel_USD
):
    channel_USD.is_active = False
    channel_USD.save()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": channel_USD.slug,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_variant_for_federation_as_customer_without_channel(
    api_client, variant
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
            },
        ],
    }

    response = api_client.post_graphql(QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables)
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_variant_for_federation_as_staff_user(
    staff_api_client, staff_user, variant, channel_USD, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": channel_USD.slug,
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductVariant",
            "id": variant_id,
            "name": variant.name,
        }
    ]


def test_query_product_variant_for_federation_as_staff_user_not_existing_channel(
    staff_api_client, staff_user, variant, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": "not-existing-channel",
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [None]


def test_query_product_variant_for_federation_as_staff_user_channel_not_active(
    staff_api_client, staff_user, variant, channel_USD, permission_manage_products
):
    channel_USD.is_active = False
    channel_USD.save()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
                "channel": channel_USD.slug,
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductVariant",
            "id": variant_id,
            "name": variant.name,
        }
    ]


def test_query_product_variant_for_federation_as_staff_user_without_chanel(
    staff_api_client, staff_user, variant, channel_USD, permission_manage_products
):
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {
        "representations": [
            {
                "__typename": "ProductVariant",
                "id": variant_id,
            },
        ],
    }

    staff_user.user_permissions.add(permission_manage_products)
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_IN_FEDERATION, variables
    )
    content = get_graphql_content(response)
    assert content["data"]["_entities"] == [
        {
            "__typename": "ProductVariant",
            "id": variant_id,
            "name": variant.name,
        }
    ]


QUERY_PRODUCT_VARIANT_WITH_ASSIGNED_ATTRIBUTE = """
query productVariant($id: ID!, $channel: String, $attrSlug: String!) {
  productVariant(id: $id, channel: $channel) {
    assignedAttribute(slug:$attrSlug){
      attribute{
        slug
      }
      ...on AssignedSingleChoiceAttribute{
        value{
          slug
        }
      }
    }
  }
}
"""


def test_product_variant_with_assigned_attribute(
    variant, channel_USD, user_api_client, size_attribute, weight_attribute
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([size_attribute, weight_attribute])

    expected_attribute_value = size_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {
            size_attribute.pk: [expected_attribute_value],
            weight_attribute.pk: [weight_attribute.values.first()],
        },
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "attrSlug": size_attribute.slug,
    }

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_WITH_ASSIGNED_ATTRIBUTE, variables
    )

    # then
    content = get_graphql_content(response)
    assigned_attribute_data = content["data"]["productVariant"]["assignedAttribute"]
    assert assigned_attribute_data["attribute"]["slug"] == size_attribute.slug
    assert assigned_attribute_data["value"]["slug"] == expected_attribute_value.slug


def test_product_variant_with_assigned_attribute_without_value(
    variant, channel_USD, user_api_client, size_attribute, weight_attribute
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([size_attribute, weight_attribute])

    associate_attribute_values_to_instance(
        variant,
        {
            size_attribute.pk: [],
            weight_attribute.pk: [weight_attribute.values.first()],
        },
    )

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "attrSlug": size_attribute.slug,
    }

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_WITH_ASSIGNED_ATTRIBUTE, variables
    )

    # then
    content = get_graphql_content(response)
    assigned_attribute_data = content["data"]["productVariant"]["assignedAttribute"]
    assert assigned_attribute_data["attribute"]["slug"] == size_attribute.slug
    assert assigned_attribute_data["value"] is None


def test_product_variant_when_assigned_attribute_is_none(
    variant, channel_USD, user_api_client, size_attribute, weight_attribute
):
    # given
    product_type = variant.product.product_type
    product_type.variant_attributes.set([size_attribute, weight_attribute])

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.id)
    variables = {
        "id": variant_id,
        "channel": channel_USD.slug,
        "attrSlug": "non-existing-slug",
    }

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_WITH_ASSIGNED_ATTRIBUTE, variables
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["productVariant"]["assignedAttribute"] is None


CHANNEL_LISTING_PRICING_FRAGMENT = """
    fragment ChannelListingPricing on ProductVariantChannelListing {
        channel {
            slug
        }
        price {
            amount
            currency
        }
        discountedPrice {
            amount
            currency
        }
        pricing {
            onSale
            price {
                gross {
                    amount
                    currency
                }
            }
            priceUndiscounted {
                gross {
                    amount
                }
            }
        }
        quantityAvailable
    }
"""

QUERY_VARIANTS_CHANNEL_LISTING_PRICING = (
    CHANNEL_LISTING_PRICING_FRAGMENT
    + """
    query VariantsChannelListingPricing($ids: [ID!]) {
        productVariants(first: 10, ids: $ids) {
            edges {
                node {
                    channelListings {
                        ...ChannelListingPricing
                    }
                }
            }
        }
    }
"""
)

QUERY_VARIANT_CHANNEL_LISTING_PRICING = (
    CHANNEL_LISTING_PRICING_FRAGMENT
    + """
    query VariantChannelListingPricing($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            channelListings {
                ...ChannelListingPricing
            }
        }
    }
"""
)

QUERY_VARIANT_PRICING_IN_CHANNEL = """
    query VariantPricingInChannel($id: ID!, $channel: String!) {
        productVariant(id: $id, channel: $channel) {
            pricing {
                onSale
                price {
                    gross {
                        amount
                        currency
                    }
                }
                priceUndiscounted {
                    gross {
                        amount
                    }
                }
            }
            quantityAvailable
        }
    }
"""


def test_channel_listing_pricing_matches_channel_scoped_pricing(
    staff_api_client,
    product_available_in_many_channels,
    permission_manage_products,
):
    """One channel-less walk returns the same pricing as one walk per channel."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    channel_listings = list(variant.channel_listings.all())
    assert len(channel_listings) == 2

    # when
    response = staff_api_client.post_graphql(
        QUERY_VARIANTS_CHANNEL_LISTING_PRICING, {"ids": [variant_id]}
    )
    content = get_graphql_content(response)

    # then
    edges = content["data"]["productVariants"]["edges"]
    assert len(edges) == 1
    listings_data = edges[0]["node"]["channelListings"]
    assert len(listings_data) == 2

    data_by_slug = {data["channel"]["slug"]: data for data in listings_data}
    for channel_listing in channel_listings:
        data = data_by_slug[channel_listing.channel.slug]
        assert data["price"]["amount"] == channel_listing.price_amount
        assert data["price"]["currency"] == channel_listing.currency

        channel_scoped = get_graphql_content(
            staff_api_client.post_graphql(
                QUERY_VARIANT_PRICING_IN_CHANNEL,
                {"id": variant_id, "channel": channel_listing.channel.slug},
            )
        )["data"]["productVariant"]

        assert data["pricing"] is not None
        assert data["pricing"] == channel_scoped["pricing"]
        assert data["quantityAvailable"] == channel_scoped["quantityAvailable"]


def test_channel_listing_discounted_price(
    staff_api_client,
    product_available_in_many_channels,
    channel_USD,
    permission_manage_products,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)

    listing = variant.channel_listings.get(channel=channel_USD)
    undiscounted_amount = Decimal("30.00")
    discounted_amount = Decimal("12.50")
    listing.price_amount = undiscounted_amount
    listing.discounted_price_amount = discounted_amount
    listing.save(update_fields=("price_amount", "discounted_price_amount"))

    # when
    response = staff_api_client.post_graphql(
        QUERY_VARIANT_CHANNEL_LISTING_PRICING,
        {"id": variant_id, "channel": channel_USD.slug},
    )
    content = get_graphql_content(response)

    # then
    listings_data = content["data"]["productVariant"]["channelListings"]
    data = next(
        data for data in listings_data if data["channel"]["slug"] == channel_USD.slug
    )
    assert data["discountedPrice"]["amount"] == discounted_amount
    assert data["discountedPrice"]["currency"] == channel_USD.currency_code
    assert data["pricing"]["priceUndiscounted"]["gross"]["amount"] == (
        undiscounted_amount
    )
    assert data["pricing"]["price"]["gross"]["amount"] == discounted_amount
    assert data["pricing"]["onSale"] is True


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", False),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            False,
        ),
        (
            "Staff user without any permission should be allowed",
            "staff_api_client",
            True,
        ),
        ("App should be allowed", "app_api_client", True),
    ],
)
def test_channel_listing_pricing_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    product_available_in_many_channels,
    channel_USD,
):
    # given
    client = request.getfixturevalue(client_fixture)
    variant = product_available_in_many_channels.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = client.post_graphql(QUERY_VARIANT_CHANNEL_LISTING_PRICING, variables)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        listings_data = content["data"]["productVariant"]["channelListings"]
        assert len(listings_data) == 2
        for data in listings_data:
            assert data["pricing"] is not None
            assert data["discountedPrice"] is not None
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"]["productVariant"]["channelListings"] is None


QUERY_PRODUCT_VARIANTS_CHANNEL_LISTING_PRICING = (
    CHANNEL_LISTING_PRICING_FRAGMENT
    + """
    query ProductVariantsChannelListingPricing($id: ID!, $channel: String) {
        product(id: $id, channel: $channel) {
            variants {
                channelListings {
                    ...ChannelListingPricing
                }
            }
        }
    }
"""
)


def _channel_listings_by_slug(api_client, query, variables, extract):
    content = get_graphql_content(api_client.post_graphql(query, variables))
    return sorted(
        extract(content["data"]), key=lambda listing: listing["channel"]["slug"]
    )


def test_channel_listing_pricing_is_the_same_across_queries(
    staff_api_client,
    product_available_in_many_channels,
    channel_USD,
    permission_manage_products,
):
    """The listing fields do not depend on the channel of the root query."""
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    product = product_available_in_many_channels
    variant = product.variants.get()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    product_id = graphene.Node.to_global_id("Product", product.pk)

    # when
    from_variant = _channel_listings_by_slug(
        staff_api_client,
        QUERY_VARIANT_CHANNEL_LISTING_PRICING,
        {"id": variant_id, "channel": channel_USD.slug},
        lambda data: data["productVariant"]["channelListings"],
    )
    from_product_in_channel = _channel_listings_by_slug(
        staff_api_client,
        QUERY_PRODUCT_VARIANTS_CHANNEL_LISTING_PRICING,
        {"id": product_id, "channel": channel_USD.slug},
        lambda data: data["product"]["variants"][0]["channelListings"],
    )
    from_product_without_channel = _channel_listings_by_slug(
        staff_api_client,
        QUERY_PRODUCT_VARIANTS_CHANNEL_LISTING_PRICING,
        {"id": product_id},
        lambda data: data["product"]["variants"][0]["channelListings"],
    )

    # then
    assert len(from_variant) == 2
    for listing_data in from_variant:
        assert listing_data["pricing"] is not None
        assert listing_data["discountedPrice"] is not None

    assert from_product_in_channel == from_variant
    assert from_product_without_channel == from_variant
