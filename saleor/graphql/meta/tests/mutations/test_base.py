from ....tests.utils import get_graphql_content


def test_handling_invalid_graphene_type(api_client):
    # given

    # This ID is invalid and represents "Che3kout:42953eb4-fa86-4e02-943f-403f47fbebe7"
    # with a typo in the type name.
    checkout_id = "Q2hlM2tvdXQ6NDI5NTNlYjQtZmE4Ni00ZTAyLTk0M2YtNDAzZjQ3ZmJlYmU3"
    query = """
        mutation UpdateMetadata($id: ID!, $input: [MetadataInput!]!) {
            updateMetadata(id: $id, input: $input) {
                errors {
                    code
                    field
                    message
                }
                item {
                    metadata {
                        key
                        value
                    }
                }
            }
        }
    """

    # when
    response = api_client.post_graphql(
        query, {"id": checkout_id, "input": [{"key": "foo", "value": "bar"}]}
    )
    response = get_graphql_content(response)

    # then
    errors = response["data"]["updateMetadata"]["errors"]
    assert errors
    assert errors[0]["field"] == "id"
    assert errors[0]["code"] == "GRAPHQL_ERROR"
    assert errors[0]["message"] == "Invalid type: Che3kout"
