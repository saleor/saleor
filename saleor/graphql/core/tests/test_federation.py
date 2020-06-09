import graphene
import pytest

from ...tests.utils import get_graphql_content


@pytest.fixture
def user_representation_by_id(staff_user):
    user_id = graphene.Node.to_global_id("User", staff_user.id)
    return {"_representations": [{"id": user_id, "__typename": "User"}]}


@pytest.fixture
def user_representation_by_email(staff_user):
    return {"_representations": [{"email": staff_user.email, "__typename": "User"}]}


FEDERATED_QUERY = """
query($_representations: [_Any!]!) {
  _entities(representations: $_representations) {
    ... on User {
      id
      email
      isStaff
    }
  }
}
"""


def test_get_user_data_through_federated_query_by_id(
    staff_api_client, user_representation_by_id, staff_user
):
    response = staff_api_client.post_graphql(FEDERATED_QUERY, user_representation_by_id)
    content = get_graphql_content(response)["data"]["_entities"]
    assert len(content) == 1
    assert content[0]["email"] == staff_user.email
    assert content[0]["isStaff"] == staff_user.is_staff


def test_get_user_data_through_federated_query_by_email(
    staff_api_client, user_representation_by_email, staff_user
):
    response = staff_api_client.post_graphql(
        FEDERATED_QUERY, user_representation_by_email
    )
    content = get_graphql_content(response)["data"]["_entities"]
    assert len(content) == 1
    assert content[0]["id"] == graphene.Node.to_global_id("User", staff_user.id)
    assert content[0]["isStaff"] == staff_user.is_staff
