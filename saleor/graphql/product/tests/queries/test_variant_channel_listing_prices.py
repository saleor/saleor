import graphene
from django.db import connection
from django.test.utils import CaptureQueriesContext

from .....attribute.models import AttributeValue
from ....tests.utils import assert_no_permission, get_graphql_content

VARIANT_CHANNEL_LISTING_PRICES_QUERY = """
    query VariantChannelListingPrices($id: ID!) {
        productVariant(id: $id) {
            channelListings {
                prices {
                    id
                    price {
                        amount
                        currency
                    }
                    customerTypes {
                        id
                        name
                    }
                    attributeValues {
                        id
                        name
                    }
                    validFrom
                    validTo
                }
            }
        }
    }
"""


def _query(client, variant):
    variables = {"id": graphene.Node.to_global_id("ProductVariant", variant.pk)}
    return client.post_graphql(VARIANT_CHANNEL_LISTING_PRICES_QUERY, variables)


def test_lists_the_rows_with_their_conditions(
    staff_api_client,
    permission_manage_products,
    variant,
    customer_type,
    loyalty_customer_attribute,
    variant_channel_listing_price,
    variant_channel_listing_price_for_customer_type,
    variant_channel_listing_price_for_attribute_value,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )
    window_row = variant_channel_listing_price
    type_row = variant_channel_listing_price_for_customer_type
    value_row = variant_channel_listing_price_for_attribute_value

    # when
    response = _query(staff_api_client, variant)

    # then
    [listing_data] = get_graphql_content(response)["data"]["productVariant"][
        "channelListings"
    ]
    assert listing_data["prices"] == [
        {
            "id": graphene.Node.to_global_id("VariantChannelListingPrice", row.pk),
            "price": {"amount": float(row.price_amount), "currency": row.currency},
            "customerTypes": customer_types,
            "attributeValues": attribute_values,
            "validFrom": row.valid_from.isoformat() if row.valid_from else None,
            "validTo": row.valid_to.isoformat() if row.valid_to else None,
        }
        for row, customer_types, attribute_values in [
            (window_row, [], []),
            (
                type_row,
                [
                    {
                        "id": graphene.Node.to_global_id(
                            "CustomerType", customer_type.pk
                        ),
                        "name": customer_type.name,
                    }
                ],
                [],
            ),
            (
                value_row,
                [],
                [
                    {
                        "id": graphene.Node.to_global_id(
                            "AttributeValue", gold_value.pk
                        ),
                        "name": gold_value.name,
                    }
                ],
            ),
        ]
    ]


def test_is_empty_without_rows(staff_api_client, permission_manage_products, variant):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)

    # when
    response = _query(staff_api_client, variant)

    # then
    [listing_data] = get_graphql_content(response)["data"]["productVariant"][
        "channelListings"
    ]
    assert listing_data["prices"] == []


def test_resolves_conditions_in_a_fixed_number_of_queries(
    staff_api_client,
    permission_manage_products,
    product_variant_list,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_products)
    gold_value = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="gold"
    )
    for variant in product_variant_list[:2]:
        listing = variant.channel_listings.first()
        row = listing.prices.create(currency=listing.currency, price_amount=5)
        row.customer_types.add(customer_type)
        row.attribute_values.add(gold_value)
    query = """
        query VariantChannelListingPrices($ids: [ID!]) {
            productVariants(first: 10, ids: $ids) {
                edges {
                    node {
                        channelListings {
                            prices {
                                customerTypes {
                                    id
                                }
                                attributeValues {
                                    id
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.pk)
            for variant in product_variant_list[:2]
        ]
    }

    # when
    with CaptureQueriesContext(connection) as ctx:
        response = staff_api_client.post_graphql(query, variables)

    # then
    edges = get_graphql_content(response)["data"]["productVariants"]["edges"]
    assert len(edges) == 2
    for edge in edges:
        [listing_data] = edge["node"]["channelListings"]
        [price_data] = listing_data["prices"]
        assert len(price_data["customerTypes"]) == 1
        assert len(price_data["attributeValues"]) == 1
    condition_queries = [
        query["sql"]
        for query in ctx.captured_queries
        if "product_variantchannellistingprice" in query["sql"]
    ]
    # the rows, the customer type conditions and the value conditions, each once
    assert len(condition_queries) == 3


def test_is_hidden_from_customers(user_api_client, variant):
    # when
    response = _query(user_api_client, variant)

    # then
    assert_no_permission(response)
