from unittest import mock

import graphene
import pytest

from .....discount.models import Voucher, VoucherChannelListing, VoucherCode
from ....tests.utils import get_graphql_content


@pytest.fixture
def voucher_list(channel_USD):
    [voucher_1, voucher_2, voucher_3] = Voucher.objects.bulk_create(
        [
            Voucher(),
            Voucher(),
            Voucher(),
        ]
    )

    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="voucher-1", voucher=voucher_1),
            VoucherCode(code="voucher-2", voucher=voucher_1),
            VoucherCode(code="voucher-3", voucher=voucher_2),
        ]
    )
    VoucherChannelListing.objects.bulk_create(
        [
            VoucherChannelListing(
                voucher=voucher_1,
                channel=channel_USD,
                discount_value=1,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=voucher_2,
                channel=channel_USD,
                discount_value=2,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=voucher_3,
                channel=channel_USD,
                discount_value=3,
                currency=channel_USD.currency_code,
            ),
        ]
    )
    return voucher_1, voucher_2, voucher_3


BULK_DELETE_VOUCHERS_MUTATION = """
    mutation voucherBulkDelete($ids: [ID!]!) {
        voucherBulkDelete(ids: $ids) {
            count
        }
    }
"""


def test_delete_vouchers(staff_api_client, voucher_list, permission_manage_discounts):
    variables = {
        "ids": [
            graphene.Node.to_global_id("Voucher", voucher.id)
            for voucher in voucher_list
        ]
    }
    response = staff_api_client.post_graphql(
        BULK_DELETE_VOUCHERS_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    assert content["data"]["voucherBulkDelete"]["count"] == 3
    assert not Voucher.objects.filter(
        id__in=[voucher.id for voucher in voucher_list]
    ).exists()


@mock.patch("saleor.graphql.discount.mutations.bulk_mutations.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_vouchers_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher_list,
    permission_manage_discounts,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("Voucher", voucher.id)
            for voucher in voucher_list
        ]
    }
    response = staff_api_client.post_graphql(
        BULK_DELETE_VOUCHERS_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    assert content["data"]["voucherBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == len(voucher_list)
