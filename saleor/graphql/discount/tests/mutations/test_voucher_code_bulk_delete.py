from unittest import mock

import graphene

from ....tests.utils import get_graphql_content

VOUCHER_CODE_BULK_DELETE_MUTATION = """
    mutation voucherCodeBulkDelete($ids: [ID!]!) {
        voucherCodeBulkDelete(ids: $ids) {
            count
            errors {
                path
                message
            }
        }
    }
"""


def test_delete_voucher_codes(staff_api_client, voucher, permission_manage_discounts):
    # given
    voucher.codes.create(code="voucher-1")
    voucher.codes.create(code="voucher-2")
    vouchers = voucher.codes.all()
    assert len(vouchers) == 3

    variables = {
        "ids": [
            graphene.Node.to_global_id("VoucherCode", code.id)
            for code in voucher.codes.all()
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CODE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)
    voucher.refresh_from_db()

    # then
    assert content["data"]["voucherCodeBulkDelete"]["count"] == 3
    assert voucher.codes.count() == 0


def test_delete_voucher_codes_as_app(
    app_api_client, voucher, permission_manage_discounts
):
    # given
    voucher.codes.create(code="voucher-1")
    voucher.codes.create(code="voucher-2")
    vouchers = voucher.codes.all()
    assert len(vouchers) == 3

    variables = {
        "ids": [
            graphene.Node.to_global_id("VoucherCode", code.id)
            for code in voucher.codes.all()
        ]
    }

    # when
    response = app_api_client.post_graphql(
        VOUCHER_CODE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)
    voucher.refresh_from_db()

    # then
    assert content["data"]["voucherCodeBulkDelete"]["count"] == 3
    assert voucher.codes.count() == 0


@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_delete_voucher_codes_trigger_voucher_codes_deleted_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    voucher,
    permission_manage_discounts,
    settings,
):
    # given
    voucher.codes.create(code="voucher-1")
    voucher.codes.create(code="voucher-2")
    codes = voucher.codes.all()
    assert len(codes) == 3

    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "ids": [
            graphene.Node.to_global_id("VoucherCode", code.id)
            for code in voucher.codes.all()
        ]
    }

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CODE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucherCodeBulkDelete"]["count"] == 3
    assert mocked_webhook_trigger.call_count == 1


def test_delete_voucher_codes_return_error_when_invalid_id(
    staff_api_client, permission_manage_discounts
):
    # given
    variables = {"ids": [graphene.Node.to_global_id("Product", 123)]}

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_CODE_BULK_DELETE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherCodeBulkDelete"]["errors"]
    assert errors
    assert errors[0]["path"] == "ids"
    assert errors[0]["message"] == "Invalid VoucherCode ID."
    assert content["data"]["voucherCodeBulkDelete"]["count"] == 0
