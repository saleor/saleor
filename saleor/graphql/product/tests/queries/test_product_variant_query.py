import graphene
from django.contrib.sites.models import Site
from measurement.measures import Weight

from .....core.units import WeightUnits
from .....warehouse import WarehouseClickAndCollectOption
from ....core.enums import WeightUnitsEnum
from ....tests.utils import assert_no_permission, get_graphql_content

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
                preorderThreshold {
                    quantity
                    soldUnits
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
            "preorderThreshold": {
                "quantity": channel_listing.preorder_quantity_threshold,
                "soldUnits": 0,
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
            "preorderThreshold": {
                "quantity": channel_listing.preorder_quantity_threshold,
                "soldUnits": 0,
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
        [
            graphene.Node.to_global_id("Stock", stock.pk) in no_address_stocks_ids
            for stock in all_stocks
        ]
    )

    # When address is given, return only stocks from warehouse that ship to that
    # address.
    assert len(data["stocksWithAddress"]) == pl_stocks.count()
    with_address_stocks_ids = [stock["id"] for stock in data["stocksWithAddress"]]
    assert all(
        [
            graphene.Node.to_global_id("Stock", stock.pk) in with_address_stocks_ids
            for stock in pl_stocks
        ]
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


QUERY_PRODUCT_VARIANT_PREORDER = """
    query ProductVariantDetails($id: ID!, $channel: String) {
        productVariant(id: $id, channel: $channel) {
            preorder {
                globalThreshold
                globalSoldUnits
                endDate
            }
        }
    }
"""


def test_get_product_variant_preorder_as_staff(
    staff_api_client,
    preorder_variant_global_and_channel_threshold,
    preorder_allocation,
    channel_USD,
    permission_manage_products,
):
    # given
    variant = preorder_variant_global_and_channel_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PREORDER,
        variables,
        permissions=[permission_manage_products],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]["preorder"]
    assert data["globalThreshold"] == variant.preorder_global_threshold
    assert data["globalSoldUnits"] == preorder_allocation.quantity
    assert data["endDate"] == variant.preorder_end_date


def test_get_product_variant_preorder_as_customer_not_allowed_fields(
    user_api_client,
    preorder_variant_global_threshold,
    channel_USD,
):
    # given
    variant = preorder_variant_global_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        QUERY_PRODUCT_VARIANT_PREORDER,
        variables,
    )

    # then
    assert_no_permission(response)


def test_get_product_variant_preorder_as_customer_allowed_fields(
    user_api_client,
    preorder_variant_global_threshold,
    channel_USD,
):
    # given
    variant = preorder_variant_global_threshold
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    query = """
        query ProductVariantDetails($id: ID!, $channel: String) {
            productVariant(id: $id, channel: $channel) {
                preorder {
                    endDate
                }
            }
        }
    """
    variables = {"id": variant_id, "channel": channel_USD.slug}

    # when
    response = user_api_client.post_graphql(
        query,
        variables,
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["productVariant"]["preorder"]
    assert data["endDate"] == variant.preorder_end_date


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
query GetProductVariantInFederation($representations: [_Any]) {
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
