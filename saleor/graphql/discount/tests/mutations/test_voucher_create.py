import json
from datetime import timedelta
from unittest.mock import patch

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
mutation  voucherCreate(
    $type: VoucherTypeEnum, $name: String, $code: String,
    $discountValueType: DiscountValueTypeEnum, $usageLimit: Int,
    $minCheckoutItemsQuantity: Int, $startDate: DateTime, $endDate: DateTime,
    $applyOncePerOrder: Boolean, $applyOncePerCustomer: Boolean) {
        voucherCreate(input: {
                name: $name, type: $type, code: $code,
                discountValueType: $discountValueType,
                minCheckoutItemsQuantity: $minCheckoutItemsQuantity,
                startDate: $startDate, endDate: $endDate, usageLimit: $usageLimit
                applyOncePerOrder: $applyOncePerOrder,
                applyOncePerCustomer: $applyOncePerCustomer}) {
            errors {
                field
                code
                message
            }
            voucher {
                type
                minCheckoutItemsQuantity
                name
                code
                discountValueType
                startDate
                endDate
                applyOncePerOrder
                applyOncePerCustomer
            }
        }
    }
"""


def test_create_voucher(staff_api_client, permission_manage_discounts):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "minCheckoutItemsQuantity": 10,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "applyOncePerOrder": True,
        "applyOncePerCustomer": True,
        "usageLimit": 3,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    get_graphql_content(response)
    voucher = Voucher.objects.get()
    assert voucher.type == VoucherType.ENTIRE_ORDER
    assert voucher.name == "test voucher"
    assert voucher.code == "testcode123"
    assert voucher.discount_value_type == DiscountValueType.FIXED
    assert voucher.start_date == start_date
    assert voucher.end_date == end_date
    assert voucher.apply_once_per_order
    assert voucher.apply_once_per_customer
    assert voucher.usage_limit == 3


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_voucher_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "testcode123",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "minCheckoutItemsQuantity": 10,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "applyOncePerOrder": True,
        "applyOncePerCustomer": True,
        "usageLimit": 3,
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    voucher = Voucher.objects.last()

    # then
    assert content["data"]["voucherCreate"]["voucher"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Voucher", voucher.id),
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
        WebhookEventAsyncType.VOUCHER_CREATED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_create_voucher_with_empty_code(staff_api_client, permission_manage_discounts):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": None,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]["voucher"]
    assert data["name"] == variables["name"]
    assert data["code"] != ""


def test_create_voucher_with_existing_gift_card_code(
    staff_api_client, gift_card, permission_manage_discounts
):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": gift_card.code,
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }

    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["errors"]
    errors = content["data"]["voucherCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors[0]["code"] == DiscountErrorCode.ALREADY_EXISTS.name


def test_create_voucher_with_existing_voucher_code(
    staff_api_client, voucher_shipping_type, permission_manage_discounts
):
    start_date = timezone.now() - timedelta(days=365)
    end_date = timezone.now() + timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": voucher_shipping_type.code,
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["errors"]
    errors = content["data"]["voucherCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "code"
    assert errors


def test_create_voucher_with_enddate_before_startdate(
    staff_api_client, voucher_shipping_type, permission_manage_discounts
):
    start_date = timezone.now() + timedelta(days=365)
    end_date = timezone.now() - timedelta(days=365)
    variables = {
        "name": "test voucher",
        "type": VoucherTypeEnum.ENTIRE_ORDER.name,
        "code": "FUTURE",
        "discountValueType": DiscountValueTypeEnum.FIXED.name,
        "discountValue": 10.12,
        "minAmountSpent": 1.12,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 3,
    }
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    assert content["data"]["voucherCreate"]["errors"]
    errors = content["data"]["voucherCreate"]["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "endDate"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors
