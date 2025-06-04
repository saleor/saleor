import graphene
import pytest

from ....tests.utils import get_graphql_content

USER_CHECKOUTS_QUERY = """
query ($userId: ID!, $filter: CheckoutFilterInput, $sortBy: CheckoutSortingInput) {
  user(id: $userId) {
    checkouts(filter: $filter, sortBy: $sortBy, first: 5) {
      edges {
        node {
          id
          updatedAt
        }
      }
    }
  }
}
"""


@pytest.mark.django_db
def test_user_checkouts_with_filter_and_sort(
    staff_api_client,
    permission_manage_users,
    user_checkout,
    channel_USD,
):
    # Give staff user permission
    staff_api_client.user.user_permissions.add(permission_manage_users)

    # Assign channel to the checkout (if needed)
    user_checkout.channel = channel_USD
    user_checkout.save()

    user_id = graphene.Node.to_global_id("User", user_checkout.user.id)
    channel_id = graphene.Node.to_global_id("Channel", channel_USD.id)
    variables = {
        "userId": user_id,
        "filter": {"channels": [channel_id]},
        "sortBy": {"field": "CREATION_DATE", "direction": "DESC"},
    }

    # When
    response = staff_api_client.post_graphql(USER_CHECKOUTS_QUERY, variables)
    content = get_graphql_content(response)

    # Then
    checkouts = content["data"]["user"]["checkouts"]["edges"]
    assert len(checkouts) >= 1
    assert checkouts[0]["node"]["id"] is not None
