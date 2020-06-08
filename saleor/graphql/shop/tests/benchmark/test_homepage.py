import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_retrieve_shop(api_client, count_queries):
    query = """
        query getShop {
          shop {
            defaultCountry {
              code
              country
            }
            countries {
              country
              code
            }
            geolocalization {
              country {
                code
                country
              }
            }
          }
        }
    """

    get_graphql_content(api_client.post_graphql(query))
