import decimal

import pytest


def _assert_error_message(response, expected_msg: str) -> None:
    data = response.json()
    assert "errors" in data, "Expected GraphQL errors, but got none"
    assert data["errors"][0]["message"] == expected_msg


@pytest.mark.django_db
def test_products_filter_price_without_channel_multiple_channels(
    staff_api_client,
    channel_USD,
    channel_PLN,
    product,
    product_with_default_variant,
):
    # given
    variant_1 = product.variants.first()
    listing_1 = variant_1.channel_listings.get(channel=channel_USD)
    listing_1.price_amount = decimal.Decimal("9.99")
    listing_1.save(update_fields=["price_amount"])

    variant_2 = product_with_default_variant.variants.first()
    listing_2 = variant_2.channel_listings.get(channel=channel_USD)
    listing_2.price_amount = decimal.Decimal("15.00")
    listing_2.save(update_fields=["price_amount"])

    query = """
        query Products($lte: Float!) {
          products(
            first: 10,
            filter: { price: { lte: $lte } }
          ) {
            edges { node { id } }
          }
        }
    """
    variables = {"lte": 10.0}

    # when
    response = staff_api_client.post_graphql(query, variables=variables)

    # then
    _assert_error_message(
        response,
        "More than one channel exists. Specify which channel to use.",
    )
