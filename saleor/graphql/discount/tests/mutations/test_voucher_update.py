import json
from unittest.mock import patch

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import DiscountValueType
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
            }
        }
    }
"""


def test_update_voucher(staff_api_client, voucher, permission_manage_discounts):
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
            "codes": [
                {"code": new_code},
            ],
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
    assert voucher.codes.count() == 2
    assert len(data["codes"]["edges"]) == 2
    assert data["discountValueType"] == DiscountValueType.PERCENTAGE.upper()
    assert data["applyOncePerOrder"] == apply_once_per_order
    assert data["singleUse"] == single_use
    assert data["minCheckoutItemsQuantity"] == 10
    assert data["usageLimit"] == 10
    assert data["codes"]["edges"][1]["node"]["code"] == new_code


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

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "codes": [
                {"code": new_code},
            ]
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucherUpdate"]["voucher"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": voucher.name,
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
    )
