from typing import Any
import pytest
import graphene

from saleor.graphql.order.types import Order

VALID_QUERY = """
query Federation ($representations: [_Any!]!) {
  _entities(representations: $representations) {
    ... on Order { number }
  }
}
"""

# Query with 'Any' instead of 'Any!' - this must not be allowed, an object must be
# provided instead.
INVALID_QUERY_NULL_LIST_ITEM = """
query Federation ($representations: [_Any]!) {
  _entities(representations: $representations) {
    ... on Order { number }
  }
}
"""

# Query with '[Any!]' instead of '[Any!]!' - this must not be allowed, the
# 'representations' argument is required.
INVALID_QUERY_NULL_LIST = """
query Federation ($representations: [_Any!]) {
  _entities(representations: $representations) {
    ... on Order { number }
  }
}
"""

# Query without the 'representations' field is not allowed, it must provide it.
INVALID_QUERY_MISSING_INPUT_FIELD = """
query Federation {
  _entities {
    ... on Order { number }
  }
}
"""


@pytest.mark.parametrize(
    ("_case", "query", "variables", "expected_error_msg"),
    [
        (
            "Error when missing 'representations' argument",
            INVALID_QUERY_MISSING_INPUT_FIELD,
            {},
            ('Argument "representations" of required type [_Any!]!" was not provided.'),
        ),
        (
            "Error when 'representations' is null",
            INVALID_QUERY_NULL_LIST,
            {"representations": None},
            (
                'Variable "representations" of type "[_Any!]" used in position '
                'expecting type "[_Any!]!".'
            ),
        ),
        (
            "Error when an *item* in 'representations' is null",
            INVALID_QUERY_NULL_LIST_ITEM,
            {"representations": [None]},
            (
                'Variable "representations" of type "[_Any]!" used in position '
                'expecting type "[_Any!]!".'
            ),
        ),
        (
            "Error when __typename is missing",
            VALID_QUERY,
            {"representations": [{"id": "foo"}]},
            "Missing required field: __typename",
        ),
        (
            "Error when __typename value is not supported",
            VALID_QUERY,
            {"representations": [{"__typename": "Invalid!"}]},
            "Invalid value or unsupported model for __typename",
        ),
        (
            "Error when __typename is incorrect type",
            VALID_QUERY,
            {"representations": [{"__typename": 1234}]},
            "Invalid type for __typename: must be a string",
        ),
    ],
)
def test_resolve_entities_handles_errors_invalid_input(
    _case,
    query: str,
    variables: dict[str, Any],
    expected_error_msg: str,
    staff_api_client,
):
    """Ensure invalid inputs are handled properly."""

    data = staff_api_client.post_graphql(query, variables).json()
    error_list = data["errors"]
    assert len(error_list) == 1

    error_dict = data["errors"][0]

    assert error_dict["message"] == expected_error_msg


def test_resolve_entities_can_only_provide_fields(staff_api_client):
    """Ensure only GraphQL fields can be provided.

    Should only be able to provide things like "id", "userEmail", ...
    and not things like `__name__`.
    """

    variables = {"representations": [{"__typename": "Order", "__name__": "foo"}]}
    data = staff_api_client.post_graphql(VALID_QUERY, variables).json()
    error_list = data["errors"]
    assert len(error_list) == 1

    error_dict = data["errors"][0]

    assert error_dict["message"] == "Unknown field for Order: __name__"

    # Sanity check: passing '__name__' to model should work
    # WARNING: must NOT raise an error - this ensures that no one changes the
    #          underlying code of ``resolve_entities()`` to a ``getattr()``
    #          which would cause us to allow non-GraphQL fields
    Order(__name__=1)


def test_resolve_entity_should_return_object_when_found(
    staff_user,
    staff_api_client,
    order_unconfirmed,
    permission_group_manage_orders,
):
    """Ensure a valid request returns the matching Order object."""

    order = order_unconfirmed
    permission_group_manage_orders.user_set.add(staff_user)

    pk = graphene.Node.to_global_id("Order", order.pk)
    variables = {"representations": [{"__typename": "Order", "id": pk}]}
    data = staff_api_client.post_graphql(
        VALID_QUERY,
        variables,
    ).json()

    assert "errors" not in data
    assert data["data"] == {"_entities": [{"number": str(order.number)}]}
