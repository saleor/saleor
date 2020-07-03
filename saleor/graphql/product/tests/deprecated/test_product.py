import warnings

import graphene

from .....channel.utils import deprecation_warning_message
from ....tests.utils import get_graphql_content

QUERY_PRODUCT = """
    query ($id: ID, $slug: String){
        product(
            id: $id,
            slug: $slug,
        ) {
            id
            name
        }
    }
    """


def test_product_query_by_id_with_default_channel(user_api_client, product):
    variables = {"id": graphene.Node.to_global_id("Product", product.pk)}

    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
        content = get_graphql_content(response)
    collection_data = content["data"]["product"]
    assert collection_data is not None
    assert collection_data["name"] == product.name
    assert any(
        [str(warning.message) == deprecation_warning_message for warning in warns]
    )


def test_product_query_by_slug_with_default_channel(user_api_client, product):
    variables = {"slug": product.slug}
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(QUERY_PRODUCT, variables=variables)
        content = get_graphql_content(response)
    collection_data = content["data"]["product"]
    assert collection_data is not None
    assert collection_data["name"] == product.name
    assert any(
        [str(warning.message) == deprecation_warning_message for warning in warns]
    )
