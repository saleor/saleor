import json
from unittest.mock import patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

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
                "code": voucher.code,
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
