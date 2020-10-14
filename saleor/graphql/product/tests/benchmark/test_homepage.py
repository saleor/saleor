import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_product_list(
    api_client, homepage_collection, category, categories_tree, count_queries,
):
    query = """
        query ProductsList {
          shop {
            description
            name
          }
          categories(level: 0, first: 4) {
            edges {
              node {
                id
                name
                backgroundImage {
                  url
                }
              }
            }
          }
        }
    """
    get_graphql_content(api_client.post_graphql(query))
