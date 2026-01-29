from typing import Any

import graphene
import pytest

QUERY = """
query Federation ($representations: [_Any!]!) {
  _entities(representations: $representations) {
    ... on Order { number }
  }
}
"""


# NOTE: happy path for the 'id' field is in ./test_schema.py
#       (test_resolve_entity_should_return_object_when_found)
@pytest.mark.parametrize(
    ("_case", "fields", "expected_error_msg"),
    [
        (
            "Error when the Graphene Type mismatches",
            {"id": graphene.Node.to_global_id("User", 1)},
            ("Invalid ID: VXNlcjox. Expected: Order, received: User."),
        ),
        (
            "Error when ID isn't UUID",
            {"id": graphene.Node.to_global_id("Order", 1)},
            ("['\u201c1\u201d is not a valid UUID.']"),
        ),
        (
            "Error when ID isn't a string",
            {"id": 123},
            ("ID must be a string"),
        ),
        (
            "Error when ID null",
            {"id": None},
            ("Missing required field: id"),
        ),
        (
            "Error when ID is blank",
            {"id": ""},
            ("Missing required field: id"),
        ),
        (
            "Error when ID is missing",
            {},
            ("Missing required field: id"),
        ),
        (
            "Error when ID isn't based64",
            {"id": "foo"},
            ("Invalid ID: foo. Expected: Order."),
        ),
    ],
)
def test_resolve_federation_references(
    _case,
    fields: dict[str, Any],
    expected_error_msg: str,
    staff_api_client,
):
    """Ensure errors are handled when user passes invalid IDs."""
    variables = {"representations": [{"__typename": "Order", **fields}]}

    data = staff_api_client.post_graphql(QUERY, variables).json()

    error_list = data["errors"]
    assert len(error_list) == 1
    assert data["errors"][0]["message"] == expected_error_msg
