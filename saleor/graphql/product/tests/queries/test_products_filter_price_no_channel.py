import decimal
import graphene
import pytest
from ....tests.utils import get_graphql_content


@pytest.mark.django_db
def test_products_filter_price_without_channel(
    staff_api_client,
    channel_USD,
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
            edges {
              node { id }
            }
          }
        }
    """
    variables = {"lte": 10.0}

    # when
    response = staff_api_client.post_graphql(query, variables=variables)

    # then
    content = get_graphql_content(response)
    returned_ids = {
        edge["node"]["id"] for edge in content["data"]["products"]["edges"]
    }

    product_id_1 = graphene.Node.to_global_id("Product", product.id)
    product_id_2 = graphene.Node.to_global_id(
        "Product", product_with_default_variant.id
    )

    assert product_id_1 in returned_ids
    assert product_id_2 not in returned_ids
