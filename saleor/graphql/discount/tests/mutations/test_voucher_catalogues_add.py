import json
from unittest.mock import patch

import graphene
import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import VoucherType
from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content
from ...mutations.voucher.catalogue_validation import VOUCHER_CATALOGUE_ITEMS_LIMIT

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


VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION = """
    mutation voucherCataloguesAdd(
        $id: ID!, $input: CatalogueInput, $catalogue: VoucherCatalogueInput
    ) {
        voucherCataloguesAdd(id: $id, input: $input, catalogue: $catalogue) {
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


def test_add_catalogue_exclusions(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    product,
    variant,
    collection,
    category,
    product_type_list,
):
    # given
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["type"])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "catalogue": {
            "productTypes": [
                graphene.Node.to_global_id("ProductType", product_type_list[0].pk)
            ],
            "excludedProducts": [graphene.Node.to_global_id("Product", product.pk)],
            "excludedVariants": [
                graphene.Node.to_global_id("ProductVariant", variant.pk)
            ],
            "excludedCollections": [
                graphene.Node.to_global_id("Collection", collection.pk)
            ],
            "excludedCategories": [graphene.Node.to_global_id("Category", category.pk)],
            "excludedProductTypes": [
                graphene.Node.to_global_id("ProductType", product_type_list[1].pk)
            ],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    assert content["data"]["voucherCataloguesAdd"]["errors"] == []
    assert list(voucher.product_types.all()) == [product_type_list[0]]
    assert list(voucher.excluded_products.all()) == [product]
    assert list(voucher.excluded_variants.all()) == [variant]
    assert list(voucher.excluded_collections.all()) == [collection]
    assert list(voucher.excluded_categories.all()) == [category]
    assert list(voucher.excluded_product_types.all()) == [product_type_list[1]]


def test_add_exclusions_to_entire_order_voucher(
    staff_api_client, voucher, permission_manage_discounts, product
):
    # given
    assert voucher.type == VoucherType.ENTIRE_ORDER
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "catalogue": {
            "excludedProducts": [graphene.Node.to_global_id("Product", product.pk)]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["voucherCataloguesAdd"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "excludedProducts"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["message"] == (
        "Exclusions are supported only by vouchers of type SPECIFIC_PRODUCT."
    )
    assert voucher.excluded_products.exists() is False


@pytest.mark.parametrize(
    ("stored_field", "added_field", "stored_field_name"),
    [
        ("products", "excludedProducts", "products"),
        ("excluded_products", "products", "excludedProducts"),
    ],
)
def test_add_item_conflicting_with_stored_catalogue(
    stored_field,
    added_field,
    stored_field_name,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    product,
):
    # given
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["type"])
    getattr(voucher, stored_field).add(product)
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "catalogue": {added_field: [product_id]},
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["voucherCataloguesAdd"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == added_field
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["message"] == (
        f"Cannot both include and exclude the same items: {product_id}. "
        f"Remove them from `{stored_field_name}` first."
    )
    assert list(voucher.products.all()) == (
        [product] if stored_field == "products" else []
    )
    assert list(voucher.excluded_products.all()) == (
        [product] if stored_field == "excluded_products" else []
    )


@pytest.mark.parametrize(
    ("field", "type_name", "model_field"),
    [
        ("excludedProductTypes", "ProductType", "excluded_product_types"),
        ("products", "Product", "products"),
    ],
)
def test_add_over_limit(
    field,
    type_name,
    model_field,
    staff_api_client,
    voucher,
    permission_manage_discounts,
):
    # given
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["type"])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "catalogue": {
            field: [
                graphene.Node.to_global_id(type_name, -pk)
                for pk in range(1, VOUCHER_CATALOGUE_ITEMS_LIMIT + 2)
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["voucherCataloguesAdd"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == field
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["message"] == (
        f"Cannot provide more than {VOUCHER_CATALOGUE_ITEMS_LIMIT} items."
    )
    assert getattr(voucher, model_field).exists() is False


def test_add_locks_voucher(
    staff_api_client, voucher, permission_manage_discounts, product_type
):
    # given
    voucher.type = VoucherType.SPECIFIC_PRODUCT
    voucher.save(update_fields=["type"])
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "catalogue": {
            "excludedProductTypes": [
                graphene.Node.to_global_id("ProductType", product_type.pk)
            ]
        },
    }

    # when
    with CaptureQueriesContext(connection) as ctx:
        response = staff_api_client.post_graphql(
            VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION,
            variables,
            permissions=[permission_manage_discounts],
        )

    # then
    content = get_graphql_content(response)
    assert content["data"]["voucherCataloguesAdd"]["errors"] == []
    assert list(voucher.excluded_product_types.all()) == [product_type]
    lock_queries = [
        query
        for query in ctx.captured_queries
        if 'FROM "discount_voucher"' in query["sql"] and "FOR UPDATE" in query["sql"]
    ]
    assert len(lock_queries) == 1


@pytest.mark.parametrize(
    ("_case", "arguments", "expected_message"),
    [
        (
            "both",
            {"input": {}, "catalogue": {}},
            "Argument 'input' cannot be combined with 'catalogue'",
        ),
        (
            "neither",
            {},
            "At least one of arguments is required: 'input', 'catalogue'.",
        ),
    ],
)
def test_add_requires_exactly_one_of_input_and_catalogue(
    _case,
    arguments,
    expected_message,
    staff_api_client,
    voucher,
    permission_manage_discounts,
):
    # given
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.pk), **arguments}

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CATALOGUES_ADD_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["voucherCataloguesAdd"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] is None
    assert errors[0]["code"] == DiscountErrorCode.GRAPHQL_ERROR.name
    assert errors[0]["message"] == expected_message
