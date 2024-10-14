from unittest import mock

import graphene

from .....discount.models import Voucher
from ....tests.utils import get_graphql_content

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
