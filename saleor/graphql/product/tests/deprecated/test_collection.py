import warnings

from .....channel.utils import DEPRECATION_WARNING_MESSAGE
from ....tests.utils import get_graphql_content


def test_collections_query_with_default_channel_slug(
    user_api_client,
    published_collection,
    unpublished_collection,
    permission_manage_products,
    channel_USD,
):
    query = """
        query Collections {
            collections(first:2) {
                edges {
                    node {
                        name
                        slug
                        description
                        products {
                            totalCount
                        }
                    }
                }
            }
        }
    """

    # query public collections only as regular user
    with warnings.catch_warnings(record=True) as warns:
        response = user_api_client.post_graphql(query)
        content = get_graphql_content(response)
    edges = content["data"]["collections"]["edges"]
    assert len(edges) == 1
    collection_data = edges[0]["node"]
    assert collection_data["name"] == published_collection.name
    assert collection_data["slug"] == published_collection.slug
    assert collection_data["description"] == published_collection.description
    assert (
        collection_data["products"]["totalCount"]
        == published_collection.products.count()
    )
    assert any(
        [str(warning.message) == DEPRECATION_WARNING_MESSAGE for warning in warns]
    )
