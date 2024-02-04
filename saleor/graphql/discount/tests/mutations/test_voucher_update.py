import json
from unittest.mock import call, patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content
from ...enums import DiscountValueTypeEnum

UPDATE_VOUCHER_MUTATION = """
mutation voucherUpdate($id: ID!, $input: VoucherInput!) {
        voucherUpdate(id: $id, input: $input) {
            errors {
                field
                code
                message
                voucherCodes
            }
            voucher {
                type
                minCheckoutItemsQuantity
                name
                usageLimit
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
                discountValueType
                startDate
                endDate
                applyOncePerOrder
                applyOncePerCustomer
                singleUse
                products(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
                variants(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
                categories(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
                collections(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }
        }
    }
"""


def test_update_voucher(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    product,
    variant,
    collection,
    category,
):
    # given
    apply_once_per_order = not voucher.apply_once_per_order
    single_use = not voucher.single_use
    # Set discount value type to 'fixed' and change it in mutation
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])
    assert voucher.codes.count() == 1

    new_code = "newCode"

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "addCodes": [new_code],
            "usageLimit": 10,
            "singleUse": single_use,
            "discountValueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "applyOncePerOrder": apply_once_per_order,
            "minCheckoutItemsQuantity": 10,
            "products": [graphene.Node.to_global_id("Product", product.pk)],
            "variants": [graphene.Node.to_global_id("ProductVariant", variant.pk)],
            "collections": [graphene.Node.to_global_id("Collection", collection.pk)],
            "categories": [graphene.Node.to_global_id("Category", category.pk)],
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]["voucher"]
    voucher.refresh_from_db()

    # then
    assert voucher.codes.count() == 2
    assert len(data["codes"]["edges"]) == 2
    assert data["discountValueType"] == DiscountValueType.PERCENTAGE.upper()
    assert data["applyOncePerOrder"] == apply_once_per_order
    assert data["singleUse"] == single_use
    assert data["minCheckoutItemsQuantity"] == 10
    assert data["usageLimit"] == 10
    assert data["codes"]["edges"][0]["node"]["code"] == new_code
    assert len(data["products"]) == 1
    assert len(data["variants"]) == 1
    assert len(data["collections"]) == 1
    assert len(data["categories"]) == 1


def test_update_voucher_without_codes(
    staff_api_client, voucher, permission_manage_discounts
):
    # given
    apply_once_per_order = not voucher.apply_once_per_order
    single_use = not voucher.single_use
    # Set discount value type to 'fixed' and change it in mutation
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save(update_fields=["discount_value_type"])
    assert voucher.codes.count() == 1

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "usageLimit": 10,
            "singleUse": single_use,
            "discountValueType": DiscountValueTypeEnum.PERCENTAGE.name,
            "applyOncePerOrder": apply_once_per_order,
            "minCheckoutItemsQuantity": 10,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]["voucher"]
    voucher.refresh_from_db()

    # then
    assert voucher.codes.count() == 1
    assert data["discountValueType"] == DiscountValueType.PERCENTAGE.upper()
    assert data["applyOncePerOrder"] == apply_once_per_order
    assert data["singleUse"] == single_use
    assert data["minCheckoutItemsQuantity"] == 10
    assert data["usageLimit"] == 10


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_voucher_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    new_code = "newCode"
    new_name = "newName"
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"addCodes": [new_code], "name": new_name},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    voucher_code = voucher.codes.last()

    voucher_updated = call(
        json.dumps(
            {
                "id": variables["id"],
                "name": new_name,
                "code": new_code,
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

    code_created = call(
        json.dumps(
            [
                {
                    "id": graphene.Node.to_global_id("VoucherCode", voucher_code.id),
                    "code": new_code,
                }
            ],
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_CODES_CREATED,
        [any_webhook],
        [voucher_code],
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    # then
    assert content["data"]["voucherUpdate"]["voucher"]
    assert mocked_webhook_trigger.call_count == 2
    assert voucher_updated in mocked_webhook_trigger.call_args_list
    assert code_created in mocked_webhook_trigger.call_args_list


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_voucher_doesnt_trigger_voucher_updated_when_only_codes_added(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]

    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]
    new_code = "newCode"
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"addCodes": [new_code]},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    voucher_code = voucher.codes.last()

    code_created = call(
        json.dumps(
            [
                {
                    "id": graphene.Node.to_global_id("VoucherCode", voucher_code.id),
                    "code": new_code,
                }
            ],
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_CODES_CREATED,
        [any_webhook],
        [voucher_code],
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    # then
    assert content["data"]["voucherUpdate"]["voucher"]
    assert mocked_webhook_trigger.call_count == 1
    assert code_created in mocked_webhook_trigger.call_args_list


def test_update_voucher_single_use_voucher_already_used_in_order(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    order,
):
    # given
    single_use = not voucher.single_use

    code_instance = voucher.codes.first()
    order.voucher_code = code_instance.code
    order.voucher = voucher
    order.save(update_fields=["voucher_code", "voucher"])

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "singleUse": single_use,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]
    errors = data["errors"]

    assert errors
    assert not data["voucher"]
    assert len(errors) == 1
    assert errors[0]["field"] == "singleUse"
    assert errors[0]["code"] == DiscountErrorCode.VOUCHER_ALREADY_USED.name
    assert not errors[0]["voucherCodes"]


def test_update_voucher_single_use_voucher_already_used_in_order_line(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    order_line,
):
    # given
    single_use = not voucher.single_use

    code_instance = voucher.codes.first()
    order_line.voucher_code = code_instance.code
    order_line.save(update_fields=["voucher_code"])

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "singleUse": single_use,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]
    errors = data["errors"]

    assert errors
    assert not data["voucher"]
    assert len(errors) == 1
    assert errors[0]["field"] == "singleUse"
    assert errors[0]["code"] == DiscountErrorCode.VOUCHER_ALREADY_USED.name
    assert not errors[0]["voucherCodes"]


def test_update_voucher_single_use_voucher_already_used_in_checkout(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    checkout,
):
    # given
    single_use = not voucher.single_use

    code_instance = voucher.codes.first()
    checkout.voucher_code = code_instance.code
    checkout.save(update_fields=["voucher_code"])

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "singleUse": single_use,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherUpdate"]
    errors = data["errors"]

    assert errors
    assert not data["voucher"]
    assert len(errors) == 1
    assert errors[0]["field"] == "singleUse"
    assert errors[0]["code"] == DiscountErrorCode.VOUCHER_ALREADY_USED.name
    assert not errors[0]["voucherCodes"]
