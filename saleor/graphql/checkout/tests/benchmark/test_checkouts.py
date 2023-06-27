import pytest

from ....tests.utils import get_graphql_content

MULTIPLE_CHECKOUT_DETAILS_QUERY = """
query multipleCheckouts {
  checkouts(first: 100){
    edges {
      node {
        id
        channel {
          id
          slug
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_staff_multiple_checkouts(
    staff_api_client,
    permission_manage_checkouts,
    permission_manage_users,
    checkouts_for_benchmarks,
    count_queries,
):
    # given
    staff_api_client.user.user_permissions.set(
        [permission_manage_checkouts, permission_manage_users]
    )

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(MULTIPLE_CHECKOUT_DETAILS_QUERY)
    )

    # then
    assert len(content["data"]["checkouts"]["edges"]) == 10
