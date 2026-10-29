import graphene

from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

QUERY_VOUCHER_BY_EXTERNAL_REFERENCE = """
    query ($id: ID, $externalReference: String) {
        voucher(
            id: $id,
            externalReference: $externalReference,
        ) {
            id
            name
            externalReference
        }
    }
    """


def test_voucher_query_by_external_reference(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    external_reference = "test-ext-ref"
    voucher.external_reference = external_reference
    voucher.save(update_fields=("external_reference",))
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"] == {
        "voucher": {
            "id": graphene.Node.to_global_id("Voucher", voucher.pk),
            "name": voucher.name,
            "externalReference": external_reference,
        }
    }


def test_voucher_query_by_external_reference_not_found(
    staff_api_client, permission_manage_discounts
):
    # given
    variables = {"externalReference": "non-existing-ext-ref"}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"] == {"voucher": None}


def test_voucher_query_by_empty_string_external_reference(
    staff_api_client, voucher, permission_manage_discounts
):
    """An empty string is treated as a missing argument, so it can't be looked up."""
    # given
    external_reference = ""
    voucher.external_reference = external_reference
    voucher.save(update_fields=("external_reference",))
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content_from_response(response)
    assert content["data"] == {"voucher": None}
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == (
        "At least one of arguments is required: 'id', 'external_reference'."
    )
    assert content["errors"][0]["path"] == ["voucher"]


def test_voucher_query_by_external_reference_no_permission(api_client, voucher):
    # given
    variables = {"externalReference": "non-existing-ext-ref"}

    # when
    response = api_client.post_graphql(QUERY_VOUCHER_BY_EXTERNAL_REFERENCE, variables)

    # then
    assert_no_permission(response)


def test_external_reference_conflicting_identifiers(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "externalReference": "voucher-reference",
    }

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response, ignore_errors=True)
    assert content["data"] == {"voucher": None}
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == (
        "Argument 'id' cannot be combined with 'external_reference'"
    )
    assert content["errors"][0]["path"] == ["voucher"]


QUERY_VOUCHER_BY_ID = """
    query Voucher($id: ID!) {
        voucher(id: $id) {
            id
            codes(first: 10){
                edges {
                    node {
                        code
                    }
                }
                pageInfo{
                    startCursor
                    endCursor
                    hasNextPage
                    hasPreviousPage
                }
            }
            name
            discountValue
        }
    }
"""


def test_staff_query_voucher(staff_api_client, voucher, permission_manage_discounts):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucher"]

    # then
    assert data["name"] == voucher.name
    assert data["codes"]["edges"][0]["node"]["code"] == voucher.codes.first().code


def test_query_voucher_by_app(app_api_client, voucher, permission_manage_discounts):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = app_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucher"]

    # then
    assert data["name"] == voucher.name
    assert data["codes"]["edges"][0]["node"]["code"] == voucher.codes.first().code


def test_query_voucher_by_customer(api_client, voucher, permission_manage_discounts):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk)}

    # when
    response = api_client.post_graphql(QUERY_VOUCHER_BY_ID, variables)

    # then
    assert_no_permission(response)


def test_staff_query_voucher_by_invalid_id(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    id = "bh/"
    variables = {"id": id}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content_from_response(response)

    # then
    assert len(content["errors"]) == 1
    assert content["errors"][0]["message"] == f"Invalid ID: {id}. Expected: Voucher."
    assert content["data"]["voucher"] is None


def test_staff_query_voucher_with_invalid_object_type(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    variables = {"id": graphene.Node.to_global_id("Order", voucher.pk)}

    # when
    response = staff_api_client.post_graphql(
        QUERY_VOUCHER_BY_ID, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucher"] is None
