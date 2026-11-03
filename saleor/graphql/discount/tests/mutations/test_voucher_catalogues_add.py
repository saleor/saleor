import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VOUCHER_CATALOGUES_ADD_MUTATION = """
    mutation voucherCataloguesAdd($id: ID!, $input: CatalogueInput!) {
        voucherCataloguesAdd(id: $id, input: $input) {
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


def test_voucher_add_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
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
        VOUCHER_CATALOGUES_ADD_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["errors"]
    assert product in voucher.products.all()
    assert category in voucher.categories.all()
    assert collection in voucher.collections.all()
    assert set(product_variant_list) == set(voucher.variants.all())


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_add_catalogues_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

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

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    # then
    assert content["data"]["voucherCataloguesAdd"]["voucher"]
    assert not data["errors"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": voucher.name,
                "code": voucher.codes.first().code,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_UPDATED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_voucher_add_no_catalogues(
    staff_api_client, voucher, permission_manage_discounts
):
    query = VOUCHER_CATALOGUES_ADD_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["errors"]
    assert not voucher.products.exists()
    assert not voucher.categories.exists()
    assert not voucher.collections.exists()
    assert not voucher.variants.exists()


def test_voucher_add_catalogues_with_product_without_variant(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    permission_manage_discounts,
):
    query = VOUCHER_CATALOGUES_ADD_MUTATION
    product.variants.all().delete()
    product_id = graphene.Node.to_global_id("Product", product.id)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    category_id = graphene.Node.to_global_id("Category", category.id)
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "products": [product_id],
            "collections": [collection_id],
            "categories": [category_id],
        },
    }

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    error = content["data"]["voucherCataloguesAdd"]["errors"][0]

    assert error["code"] == DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.name
    assert error["message"] == "Cannot manage products without variants."


def test_voucher_remove_no_catalogues(
    staff_api_client,
    voucher,
    category,
    product,
    collection,
    product_variant_list,
    permission_manage_discounts,
):
    # given
    voucher.products.add(product)
    voucher.collections.add(collection)
    voucher.categories.add(category)
    voucher.variants.add(*product_variant_list)

    query = VOUCHER_CATALOGUES_ADD_MUTATION
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"products": [], "collections": [], "categories": [], "variants": []},
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherCataloguesAdd"]

    assert not data["errors"]
    assert voucher.products.exists()
    assert voucher.categories.exists()
    assert voucher.collections.exists()
    assert voucher.variants.exists()


VOUCHER_CATALOGUES_ADD_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation voucherCataloguesAdd(
        $id: ID, $externalReference: String, $input: CatalogueInput!
    ) {
        voucherCataloguesAdd(
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
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = {
        "externalReference": external_reference,
        "input": {"products": [graphene.Node.to_global_id("Product", product.pk)]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherCataloguesAdd"]
    assert data["errors"] == []
    assert data["voucher"] == {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "externalReference": external_reference,
    }
    assert list(voucher.products.all()) == [product]
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
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Voucher", voucher.pk)
    variables["input"] = {
        "products": [graphene.Node.to_global_id("Product", product.pk)]
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    data = get_graphql_content(response)["data"]["voucherCataloguesAdd"]
    assert data["voucher"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    assert voucher.products.exists() is False
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
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = {
        "externalReference": external_reference,
        "input": {"products": [graphene.Node.to_global_id("Product", product.pk)]},
    }

    # when
    response = client.post_graphql(
        VOUCHER_CATALOGUES_ADD_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherCataloguesAdd"]
        assert data["errors"] == []
        assert data["voucher"] == {
            "id": graphene.Node.to_global_id("Voucher", voucher.pk),
            "externalReference": external_reference,
        }
        assert list(voucher.products.all()) == [product]
        webhook.assert_called_once_with(voucher, voucher.code)
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherCataloguesAdd": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherCataloguesAdd"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: "
            "MANAGE_DISCOUNTS"
        )
        assert voucher.products.exists() is False
        webhook.assert_not_called()
