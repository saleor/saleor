import graphene

from ...tests.utils import get_graphql_content


def test_product_prior_price(api_client, product, channel_USD):
    # given
    query = """
        query ProductWithPriorPrice($id: ID!, $channel: String!) {
            product(id: $id, channel: $channel) {
                pricing {
                    priceRangePrior {
                        start {
                            gross {
                                amount
                                currency
                            }
                        }
                    }
                }
            }
        }
    """
    variant = product.variants.first()
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "channel": channel_USD.slug,
    }

    # when
    response = api_client.post_graphql(query, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["product"]
    price_range = data["pricing"]["priceRangePrior"]
    assert price_range is not None
    assert (
        price_range["start"]["gross"]["amount"]
        == variant.channel_listings.first().prior_price_amount
    )
