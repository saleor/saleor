from unittest.mock import ANY

import pytest
from django_countries import countries

from ....tests.utils import get_graphql_content

VOUCHERS_QUERY = """
    query vouchers {
        vouchers(first: 1) {
            edges {
                node {
                    type
                    name
                    code
                    usageLimit
                    used
                    startDate
                    discountValueType
                    applyOncePerCustomer
                    products(first: 1) {
                        edges {
                            node {
                                name
                            }
                        }
                    }
                    countries {
                        code
                        country
                    }
                    channelListings {
                        id
                        channel {
                            slug
                        }
                        discountValue
                        currency
                    }
                }
            }
        }
    }
"""


@pytest.fixture
def voucher_with_many_channels_and_countries(voucher_with_many_channels):
    voucher_with_many_channels.countries = countries
    voucher_with_many_channels.save(update_fields=["countries"])
    return voucher_with_many_channels


def test_voucher_query(
    staff_api_client,
    voucher,
    product,
    permission_manage_discounts,
    permission_manage_products,
):
    query = VOUCHERS_QUERY
    voucher.products.add(product)
    code = voucher.codes.first()
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"][0]["node"]

    assert data["type"] == voucher.type.upper()
    assert data["name"] == voucher.name
    assert data["code"] == code.code
    assert data["usageLimit"] == voucher.usage_limit
    assert data["products"]["edges"][0]["node"]["name"] == product.name

    assert data["applyOncePerCustomer"] == voucher.apply_once_per_customer
    assert data["used"] == code.used
    assert data["startDate"] == voucher.start_date.isoformat()
    assert data["discountValueType"] == voucher.discount_value_type.upper()
    assert data["countries"] == [
        {"country": country.name, "code": country.code} for country in voucher.countries
    ]
    channel_listing = voucher.channel_listings.first()
    assert {
        "id": ANY,
        "channel": {"slug": channel_listing.channel.slug},
        "discountValue": channel_listing.discount_value,
        "currency": channel_listing.channel.currency_code,
    } in data["channelListings"]


def test_voucher_query_no_codes(
    staff_api_client,
    voucher,
    product,
    permission_manage_discounts,
    permission_manage_products,
):
    query = VOUCHERS_QUERY
    voucher.products.add(product)
    voucher.codes.all().delete()
    # This simulates edge case when we don't have any codes assigned to voucher
    assert len(voucher.codes.all()) == 0

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts, permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"][0]["node"]

    assert data["type"] == voucher.type.upper()
    assert data["name"] == voucher.name
    assert data["code"] is None
    # check if used function is calculated properly even if we don't have code assigned
    # to voucher
    assert data["used"] == 0
    assert data["usageLimit"] == voucher.usage_limit
    assert data["products"]["edges"][0]["node"]["name"] == product.name


def test_voucher_query_with_channel_slug(
    staff_api_client,
    voucher_with_many_channels_and_countries,
    permission_manage_discounts,
    channel_USD,
    product,
):
    voucher = voucher_with_many_channels_and_countries
    voucher.products.add(product)
    code = voucher.codes.first()

    query = VOUCHERS_QUERY
    variables = {"channel": channel_USD.slug}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["vouchers"]["edges"][0]["node"]

    assert data["type"] == voucher.type.upper()
    assert data["name"] == voucher.name
    assert data["code"] == code.code
    assert data["products"]["edges"][0]["node"]["name"] == product.name
    assert data["usageLimit"] == voucher.usage_limit
    assert data["applyOncePerCustomer"] == voucher.apply_once_per_customer
    assert data["used"] == code.used
    assert data["startDate"] == voucher.start_date.isoformat()
    assert data["discountValueType"] == voucher.discount_value_type.upper()
    assert data["countries"] == [
        {"country": country.name, "code": country.code} for country in voucher.countries
    ]
    assert len(data["channelListings"]) == 2
    for channel_listing in voucher.channel_listings.all():
        assert {
            "id": ANY,
            "channel": {"slug": channel_listing.channel.slug},
            "discountValue": channel_listing.discount_value,
            "currency": channel_listing.channel.currency_code,
        } in data["channelListings"]


def test_vouchers_query_with_channel_slug(
    staff_api_client,
    voucher_percentage,
    voucher_with_many_channels,
    permission_manage_discounts,
    channel_PLN,
    product,
):
    query = """
    query vouchers($channel: String) {
        vouchers(first: 2, channel: $channel) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    variables = {"channel": channel_PLN.slug}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["vouchers"]["edges"]) == 1


def test_vouchers_query(
    staff_api_client,
    voucher_percentage,
    voucher_with_many_channels,
    permission_manage_discounts,
    channel_PLN,
    product,
):
    query = """
    query vouchers {
        vouchers(first: 2) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """

    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert len(content["data"]["vouchers"]["edges"]) == 2
