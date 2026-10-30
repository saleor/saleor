import graphene
import pytest

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


QUERY_VOUCHER_CATALOGUE = """
    query ($id: ID) {
        voucher(id: $id) {
            productTypes(first: 10) { edges { node { id } } }
            excludedProducts(first: 10) { edges { node { id } } }
            excludedVariants(first: 10) { edges { node { id } } }
            excludedCollections(first: 10) { edges { node { id } } }
            excludedCategories(first: 10) { edges { node { id } } }
            excludedProductTypes(first: 10) { edges { node { id } } }
        }
    }
"""


def _connection(type_name, instance):
    return {
        "edges": [{"node": {"id": graphene.Node.to_global_id(type_name, instance.pk)}}]
    }


@pytest.mark.parametrize(
    ("_case", "client_fixture", "permission_fixture", "is_allowed"),
    [
        ("Unauthenticated user should be rejected", "api_client", None, False),
        (
            "Authenticated unprivileged user (non-staff) should be rejected",
            "user_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/o the permission should be rejected",
            "staff_api_client",
            None,
            False,
        ),
        (
            "Authenticated user w/ the correct permission should be allowed",
            "staff_api_client",
            "permission_manage_discounts",
            True,
        ),
    ],
)
def test_catalogue_fields_authorization(
    _case,
    client_fixture,
    permission_fixture,
    is_allowed,
    request,
    voucher_with_exclusions,
    product,
    variant,
    collection,
    category,
    product_type_list,
):
    # given
    client = request.getfixturevalue(client_fixture)
    if permission_fixture:
        client.user.user_permissions.add(request.getfixturevalue(permission_fixture))
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher_with_exclusions.pk)
    }

    # when
    response = client.post_graphql(QUERY_VOUCHER_CATALOGUE, variables)

    # then
    if is_allowed:
        content = get_graphql_content(response)
        assert content["data"]["voucher"] == {
            "productTypes": _connection("ProductType", product_type_list[0]),
            "excludedProducts": _connection("Product", product),
            "excludedVariants": _connection("ProductVariant", variant),
            "excludedCollections": _connection("Collection", collection),
            "excludedCategories": _connection("Category", category),
            "excludedProductTypes": _connection("ProductType", product_type_list[1]),
        }
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucher": None}


QUERY_ORDER_VOUCHER_CATALOGUE = """
    query ($id: ID!) {
        order(id: $id) {
            voucher {
                categories(first: 10) { edges { node { id } } }
                excludedCategories(first: 10) { edges { node { id } } }
                productTypes(first: 10) { edges { node { id } } }
                excludedProducts(first: 10) { edges { node { id } } }
                excludedVariants(first: 10) { edges { node { id } } }
                excludedCollections(first: 10) { edges { node { id } } }
                excludedProductTypes(first: 10) { edges { node { id } } }
            }
        }
    }
"""


def test_excluded_categories_public_like_categories(
    staff_api_client,
    permission_manage_orders,
    order,
    voucher_with_exclusions,
    category,
    category_list,
):
    # given
    order.voucher = voucher_with_exclusions
    order.save(update_fields=["voucher"])
    included_category = category_list[0]
    voucher_with_exclusions.categories.add(included_category)
    staff_api_client.user.user_permissions.add(permission_manage_orders)
    variables = {"id": graphene.Node.to_global_id("Order", order.pk)}

    # when
    response = staff_api_client.post_graphql(QUERY_ORDER_VOUCHER_CATALOGUE, variables)

    # then
    content = get_graphql_content_from_response(response)
    restricted_fields = [
        "productTypes",
        "excludedProducts",
        "excludedVariants",
        "excludedCollections",
        "excludedProductTypes",
    ]
    assert sorted(error["path"][-1] for error in content["errors"]) == sorted(
        restricted_fields
    )
    assert {
        error["extensions"]["exception"]["code"] for error in content["errors"]
    } == {"PermissionDenied"}
    assert content["data"]["order"]["voucher"] == {
        "categories": _connection("Category", included_category),
        "excludedCategories": _connection("Category", category),
        **dict.fromkeys(restricted_fields),
    }
