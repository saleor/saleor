import pytest
from django.test import override_settings

from ..core.exceptions import ReadOnlyException
from .tests.utils import get_graphql_content


@override_settings(
    GRAPHENE={"MIDDLEWARE": ["saleor.graphql.middleware.ReadOnlyMiddleware"]}
)
def test_read_only_middleware_blocked_mutation(staff_api_client):
    mutation = """
        mutation updateMetadata($id: ID!, $input: [MetadataInput!]!) {
            updateMetadata(id: $id, input: $input) {
                errors {
                    code
                }
            }
        }
    """
    response = staff_api_client.post_graphql(
        mutation, {"id": "anything", "input": [{"key": "key", "value": "value"}]}
    )
    content = get_graphql_content(response, ignore_errors=True)
    assert (
        content["errors"][0]["extensions"]["exception"]["code"]
        == ReadOnlyException.__name__
    )


@override_settings(
    GRAPHENE={"MIDDLEWARE": ["saleor.graphql.middleware.ReadOnlyMiddleware"]}
)
def test_read_only_middleware_allowed_mutation(staff_api_client, customer_user):
    mutation = """
        mutation tokenCreate($email: String!, $password: String!){
            tokenCreate(email: $email, password: $password) {
                token
            }
        }
    """
    response = staff_api_client.post_graphql(
        mutation, {"email": customer_user.email, "password": customer_user._password}
    )
    content = get_graphql_content(response)
    assert content["data"]["tokenCreate"]["token"]


@override_settings(GRAPHENE={"MIDDLEWARE": ["saleor.graphql.middleware.NonExisting"]})
def test_middleware_invalid_name(api_client):
    with pytest.raises(ImportError):
        api_client.post_graphql("")
