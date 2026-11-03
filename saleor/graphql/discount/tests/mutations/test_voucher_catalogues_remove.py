import graphene
import pytest

from .....discount.error_codes import DiscountErrorCode
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VOUCHER_REMOVE_CATALOGUES = """
    mutation voucherCataloguesRemove($id: ID!, $input: CatalogueInput!) {
        voucherCataloguesRemove(id: $id, input: $input) {
            voucher {
                name
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_voucher_remove_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)
    voucher.variants.add(*product_variant_list)

    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variant_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.id)
        for variant in product_variant_list
    ]
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
            "variants": variant_ids,
        },
    }

    response = staff_api_client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesRemove"]
    voucher_variants = list(voucher.variants.all())

    assert not data["errors"]
    assert product not in voucher.products.all()
    assert category not in voucher.categories.all()
    assert collection not in voucher.collections.all()
    assert not any(v in voucher_variants for v in product_variant_list)


VOUCHER_REMOVE_CATALOGUES_BY_EXTERNAL_REFERENCE = """
    mutation voucherCataloguesRemove(
        $id: ID, $externalReference: String, $input: CatalogueInput!
    ) {
        voucherCataloguesRemove(
            id: $id, externalReference: $externalReference, input: $input
        ) {
            voucher {
                id
                externalReference
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_by_external_reference(
    staff_api_client, voucher, product, permission_manage_discounts, mocker
):
    # given
    external_reference = "test-ext-ref"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    voucher.products.add(product)
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = {
        "externalReference": external_reference,
        "input": {"products": [graphene.Node.to_global_id("Product", product.pk)]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherCataloguesRemove"]
    assert data["errors"] == []
    assert data["voucher"] == {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "externalReference": external_reference,
    }
    assert voucher.products.exists() is False
    webhook.assert_called_once_with(voucher, voucher.code)


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'externalReference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'externalReference'",
        ),
        (
            "not_found",
            {"externalReference": "missing-reference"},
            "externalReference",
            DiscountErrorCode.NOT_FOUND,
            "Couldn't resolve to a node: missing-reference",
        ),
    ],
)
def test_external_reference_invalid_identifiers(
    _case,
    identifiers,
    error_field,
    error_code,
    message,
    staff_api_client,
    voucher,
    product,
    permission_manage_discounts,
    mocker,
):
    # given
    voucher.external_reference = "existing-reference"
    voucher.save(update_fields=("external_reference",))
    voucher.products.add(product)
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Voucher", voucher.pk)
    variables["input"] = {
        "products": [graphene.Node.to_global_id("Product", product.pk)]
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    data = get_graphql_content(response)["data"]["voucherCataloguesRemove"]
    assert data["voucher"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert list(voucher.products.all()) == [product]
    webhook.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "client_fixture", "is_allowed"),
    [
        ("anonymous", "api_client", False),
        ("customer", "user_api_client", False),
        ("staff_without_permission", "staff_api_client", False),
        ("staff_with_permission", "staff_api_client", True),
        ("app_without_permission", "app_api_client", False),
        ("app_with_permission", "app_api_client", True),
    ],
)
def test_external_reference_authorization(
    _case,
    client_fixture,
    is_allowed,
    request,
    voucher,
    product,
    permission_manage_discounts,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    external_reference = "existing-reference"
    voucher.external_reference = external_reference
    voucher.save(update_fields=("external_reference",))
    voucher.products.add(product)
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = {
        "externalReference": external_reference,
        "input": {"products": [graphene.Node.to_global_id("Product", product.pk)]},
    }

    # when
    response = client.post_graphql(
        VOUCHER_REMOVE_CATALOGUES_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherCataloguesRemove"]
        assert data["errors"] == []
        assert data["voucher"] == {
            "id": graphene.Node.to_global_id("Voucher", voucher.pk),
            "externalReference": external_reference,
        }
        assert voucher.products.exists() is False
        webhook.assert_called_once_with(voucher, voucher.code)
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherCataloguesRemove": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherCataloguesRemove"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_DISCOUNTS"
        )
        assert list(voucher.products.all()) == [product]
        webhook.assert_not_called()
