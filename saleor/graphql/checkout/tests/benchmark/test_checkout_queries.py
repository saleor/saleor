import pytest

from ....tests.utils import get_graphql_content


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_user_checkout_with_associated_discounts(
    user_api_client, checkout_with_discounts, count_queries
):
    # given
    query = """
        query {
          me {
            checkout {
              id
              discounts{
                id
                name
              }
            }
          }
        }
    """

    # when
    data = get_graphql_content(user_api_client.post_graphql(query))

    # then
    assert len(data["data"]["me"]["checkout"]["discounts"]) > 0
