import json
from datetime import timedelta
from unittest.mock import call, patch

import graphene
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import DiscountValueType, VoucherType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Voucher
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content
from ...enums import DiscountValueTypeEnum, VoucherTypeEnum

CREATE_VOUCHER_MUTATION = """
mutation voucherCreate($input: VoucherInput!) {
        voucherCreate(input: $input) {
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
                used
                codes(first: 10){
                    edges {
                        node {
                            code
                            used
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
            }
        }
    }
"""


def test_create_voucher(
    staff_api_client,
    permission_manage_discounts,
    product,
    variant,
    collection,
    category,
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)

    name = "test voucher"
    variables = {
        "input": {
            "name": name,
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": ["testcode123", "testcode456"],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "minCheckoutItemsQuantity": 10,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "applyOncePerOrder": True,
            "applyOncePerCustomer": True,
            "singleUse": True,
            "usageLimit": 3,
            "products": [graphene.Node.to_global_id("Product", product.pk)],
            "variants": [graphene.Node.to_global_id("ProductVariant", variant.pk)],
            "collections": [graphene.Node.to_global_id("Collection", collection.pk)],
            "categories": [graphene.Node.to_global_id("Category", category.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    voucher = Voucher.objects.get()
    codes = voucher.codes.all()

    # then
    assert not data["errors"]
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.name == name
    assert voucher.discount_value_type == DiscountValueType.FIXED
    assert voucher.start_date == start_date
    assert voucher.end_date == end_date
    assert voucher.apply_once_per_order
    assert voucher.apply_once_per_customer
    assert voucher.single_use
    assert voucher.usage_limit == 3
    assert len(voucher.products.all()) == 1
    assert len(voucher.variants.all()) == 1
    assert len(voucher.collections.all()) == 1
    assert len(voucher.categories.all()) == 1
    assert data["voucher"]["usageLimit"] == 3
    assert len(codes) == 2


def test_create_voucher_no_codes(
    staff_api_client,
    permission_manage_discounts,
    product,
    variant,
    collection,
    category,
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)

    name = "test voucher"
    variables = {
        "input": {
            "name": name,
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": [""],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "minCheckoutItemsQuantity": 10,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "applyOncePerOrder": True,
            "applyOncePerCustomer": True,
            "singleUse": True,
            "usageLimit": 3,
            "products": [graphene.Node.to_global_id("Product", product.pk)],
            "variants": [graphene.Node.to_global_id("ProductVariant", variant.pk)],
            "collections": [graphene.Node.to_global_id("Collection", collection.pk)],
            "categories": [graphene.Node.to_global_id("Category", category.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    assert not data["errors"]
    voucher = Voucher.objects.get()

    assert voucher.name == name
    assert voucher.type == VoucherType.ENTIRE_ORDER
    # check if used function is calculated properly
    assert data["voucher"]["used"] == 0
    assert data["voucher"]["usageLimit"] == 3


def test_create_voucher_return_error_when_code_and_codes_args_combined(
    staff_api_client, permission_manage_discounts
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)

    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "code": "testcode123",
            "addCodes": ["testcode123", "testcode456"],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "minCheckoutItemsQuantity": 10,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "applyOncePerOrder": True,
            "applyOncePerCustomer": True,
            "usageLimit": 3,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]

    # then
    message = "Argument 'code' cannot be combined with 'addCodes'"
    assert data["errors"]
    assert data["errors"][0]["code"] == DiscountErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["message"] == message


def test_create_voucher_return_error_when_code_or_codes_arg_not_in_input(
    staff_api_client, permission_manage_discounts
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)

    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "minCheckoutItemsQuantity": 10,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "applyOncePerOrder": True,
            "applyOncePerCustomer": True,
            "usageLimit": 3,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]

    # then
    message = "At least one of arguments is required: 'code', 'addCodes'."
    assert data["errors"]
    assert data["errors"][0]["code"] == DiscountErrorCode.GRAPHQL_ERROR.name
    assert data["errors"][0]["message"] == message


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_voucher_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_voucher_event,
    any_webhook,
    staff_api_client,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_voucher_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)

    code_1 = "testcode123"
    code_2 = "testcode456"

    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": [code_1, code_2],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "minCheckoutItemsQuantity": 10,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "applyOncePerOrder": True,
            "applyOncePerCustomer": True,
            "usageLimit": 3,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    voucher = Voucher.objects.last()

    voucher_created = call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Voucher", voucher.id),
                "name": voucher.name,
                "code": code_2,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_CREATED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )

    new_codes = voucher.codes.filter(code__in=[code_1, code_2])
    codes_created = call(
        json.dumps(
            [
                {
                    "id": graphene.Node.to_global_id("VoucherCode", code.id),
                    "code": code.code,
                }
                for code in new_codes
            ],
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_CODES_CREATED,
        [any_webhook],
        list(new_codes),
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    # then
    assert content["data"]["voucherCreate"]
    assert mocked_webhook_trigger.call_count == 2
    assert voucher_created in mocked_webhook_trigger.call_args_list
    assert codes_created in mocked_webhook_trigger.call_args_list


def test_create_voucher_with_empty_code(staff_api_client, permission_manage_discounts):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": [{"code": ""}],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "usageLimit": None,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]["voucher"]

    # then
    assert data["name"] == variables["input"]["name"]
    assert len(data["codes"]["edges"]) == 1
    assert data["codes"]["edges"][0]["node"]["code"] != ""


def test_create_voucher_with_spaces_in_code(
    staff_api_client, permission_manage_discounts
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": ["  PROMO"],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "usageLimit": None,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]["voucher"]

    # then
    assert data["name"] == variables["input"]["name"]
    assert len(data["codes"]["edges"]) == 1
    assert data["codes"]["edges"][0]["node"]["code"] == "PROMO"


def test_create_voucher_with_duplicated_codes(
    staff_api_client, permission_manage_discounts
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": ["CODE", "CODE"],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "usageLimit": None,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    errors = data["errors"]

    # then
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "codes"
    assert errors[0]["code"] == DiscountErrorCode.DUPLICATED_INPUT_ITEM.name
    assert errors[0]["voucherCodes"] == ["CODE"]


def test_create_voucher_with_existing_gift_card_code(
    staff_api_client, gift_card, permission_manage_discounts
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": [gift_card.code],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "minCheckoutItemsQuantity": 10,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "applyOncePerOrder": True,
            "applyOncePerCustomer": True,
            "usageLimit": 3,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    errors = content["data"]["voucherCreate"]["errors"]

    # when
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "codes"
    assert errors[0]["code"] == DiscountErrorCode.ALREADY_EXISTS.name
    assert errors[0]["voucherCodes"] == [gift_card.code]


def test_create_voucher_with_existing_voucher_code(
    staff_api_client, voucher_shipping_type, permission_manage_discounts
):
    # given
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    code = voucher_shipping_type.codes.first().code
    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": [code],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "usageLimit": 3,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    errors = content["data"]["voucherCreate"]["errors"]

    # then
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "codes"
    assert errors[0]["voucherCodes"] == [code]


def test_create_voucher_with_enddate_before_startdate(
    staff_api_client, permission_manage_discounts
):
    # given
    start_date = timezone.now() + timedelta(days=365)
    end_date = timezone.now() - timedelta(days=365)

    variables = {
        "input": {
            "name": "test voucher",
            "type": VoucherTypeEnum.ENTIRE_ORDER.name,
            "addCodes": ["testcode123"],
            "discountValueType": DiscountValueTypeEnum.FIXED.name,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "usageLimit": 3,
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]

    # then
    errors = data["errors"]
    assert errors
    assert len(errors) == 1
    assert errors[0]["field"] == "endDate"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
