import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Voucher
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)

VOUCHER_DELETE_MUTATION = """
    mutation DeleteVoucher($id: ID!) {
        voucherDelete(id: $id) {
            voucher {
                name
                id
            }
            errors {
                field
                code
                message
            }
          }
        }
"""

DELETE_VOUCHER_BY_EXTERNAL_REFERENCE_MUTATION = """
    mutation deleteVoucher($id: ID, $externalReference: String) {
        voucherDelete(id: $id, externalReference: $externalReference) {
            voucher {
                name
                externalReference
            }
            errors {
                field
                message
                code
            }
        }
    }
"""


def test_by_external_reference(staff_api_client, voucher, permission_manage_discounts):
    # given
    external_reference = "test-ext-ref"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    variables = {"externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        DELETE_VOUCHER_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherDelete"]
    assert data["errors"] == []
    assert data["voucher"]["name"] == voucher.name
    assert data["voucher"]["externalReference"] == external_reference
    assert Voucher.objects.filter(pk=voucher.pk).exists() is False


@pytest.mark.parametrize(
    ("_case", "identifiers", "error_field", "error_code", "message"),
    [
        (
            "omitted",
            {},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "null",
            {"id": None, "externalReference": None},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "empty",
            {"externalReference": ""},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "At least one of arguments is required: 'id', 'external_reference'.",
        ),
        (
            "both",
            {"externalReference": "existing-reference"},
            None,
            DiscountErrorCode.GRAPHQL_ERROR,
            "Argument 'id' cannot be combined with 'external_reference'",
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
    permission_manage_discounts,
    mocker,
):
    # given
    voucher.external_reference = "existing-reference"
    voucher.save(update_fields=("external_reference",))
    original_name = voucher.name
    original_reference = voucher.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_deleted")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Voucher", voucher.pk)

    # when
    response = staff_api_client.post_graphql(
        DELETE_VOUCHER_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["voucherDelete"]
    assert data["voucher"] is None
    assert len(data["errors"]) == 1
    assert data["errors"][0] == {
        "field": error_field,
        "code": error_code.name,
        "message": message,
    }
    voucher.refresh_from_db(fields=("name", "external_reference"))
    assert voucher.name == original_name
    assert voucher.external_reference == original_reference
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
    permission_manage_discounts,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    voucher.external_reference = "existing-reference"
    voucher.save(update_fields=("external_reference",))
    original_name = voucher.name
    original_reference = voucher.external_reference
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_deleted")
    variables = {"externalReference": original_reference}

    # when
    response = client.post_graphql(
        DELETE_VOUCHER_BY_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherDelete"]
        assert data["errors"] == []
        assert Voucher.objects.filter(pk=voucher.pk).exists() is False
        assert data["voucher"] == {
            "name": original_name,
            "externalReference": original_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherDelete": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherDelete"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_DISCOUNTS"
        )
        voucher.refresh_from_db(fields=("name", "external_reference"))
        assert voucher.name == original_name
        assert voucher.external_reference == original_reference
        webhook.assert_not_called()


def test_voucher_delete_mutation(
    staff_api_client, voucher, permission_manage_discounts
):
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.id)}

    response = staff_api_client.post_graphql(
        VOUCHER_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)
    data = content["data"]["voucherDelete"]
    assert data["voucher"]["name"] == voucher.name
    with pytest.raises(voucher._meta.model.DoesNotExist):
        voucher.refresh_from_db()


@freeze_time("2022-05-12 12:00:00")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_voucher_delete_mutation_trigger_webhook(
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
    voucher_code = voucher.codes.first()
    variables = {"id": graphene.Node.to_global_id("Voucher", voucher.id)}

    # when
    response = staff_api_client.post_graphql(
        VOUCHER_DELETE_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert content["data"]["voucherDelete"]["voucher"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": voucher.name,
                "code": voucher_code.code,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.VOUCHER_DELETED,
        [any_webhook],
        voucher,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )
