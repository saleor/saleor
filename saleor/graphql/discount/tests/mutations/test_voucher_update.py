import json
from unittest.mock import call, patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import DiscountValueType
from .....discount.error_codes import DiscountErrorCode
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import DiscountValueTypeEnum

MUTATION_UPDATE_VOUCHER_BY_EXTERNAL_REFERENCE = """
    mutation updateVoucher(
        $id: ID, $externalReference: String, $input: VoucherInput!
    ) {
        voucherUpdate(
            id: $id, externalReference: $externalReference, input: $input
        ) {
            errors {
                message
                field
                code
            }
            voucher {
                name
                externalReference
            }
        }
    }
"""


def test_by_external_reference(staff_api_client, voucher, permission_manage_discounts):
    # given
    external_reference = "test-ext-ref"
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])
    name = "New name"
    variables = {
        "externalReference": external_reference,
        "input": {"name": name},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherUpdate"]
    assert data["errors"] == []
    voucher.refresh_from_db(fields=("name", "external_reference"))
    assert data["voucher"]["name"] == name
    assert voucher.name == name
    assert voucher.external_reference == external_reference


def test_with_non_unique_external_reference(
    staff_api_client, voucher, voucher_list, permission_manage_discounts
):
    # given
    external_reference = "test-ext-ref"
    other_voucher = voucher_list[0]
    other_voucher.external_reference = external_reference
    other_voucher.save(update_fields=["external_reference"])

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.pk),
        "input": {"externalReference": external_reference},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherUpdate"]
    voucher.refresh_from_db(fields=("external_reference",))
    assert voucher.external_reference is None
    assert data["voucher"] is None
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"] == "Voucher with this External reference already exists."
    )
    assert errors[0]["field"] == "externalReference"
    assert errors[0]["code"] == DiscountErrorCode.UNIQUE.name


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
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = dict(identifiers)
    if _case == "both":
        variables["id"] = graphene.Node.to_global_id("Voucher", voucher.pk)
    variables["input"] = {"name": "Changed name"}

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
        check_no_permissions=False,
    )

    # then
    data = get_graphql_content(response)["data"]["voucherUpdate"]
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
    name = "Changed voucher"
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_updated")
    variables = {"externalReference": original_reference, "input": {"name": name}}

    # when
    response = client.post_graphql(
        MUTATION_UPDATE_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherUpdate"]
        assert data["errors"] == []
        voucher.refresh_from_db(fields=("name", "external_reference"))
        assert voucher.name == name
        assert voucher.external_reference == original_reference
        assert data["voucher"] == {
            "name": name,
            "externalReference": original_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherUpdate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherUpdate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_DISCOUNTS"
        )
        voucher.refresh_from_db(fields=("name", "external_reference"))
        assert voucher.name == original_name
        assert voucher.external_reference == original_reference
        webhook.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "reference_input", "expected_reference"),
    [
        ("changed", {"externalReference": "new-reference"}, "new-reference"),
        ("cleared", {"externalReference": None}, None),
        ("omitted", {}, "original-reference"),
    ],
)
def test_external_reference_input(
    _case,
    reference_input,
    expected_reference,
    staff_api_client,
    voucher,
    permission_manage_discounts,
):
    # given
    voucher.external_reference = "original-reference"
    voucher.save(update_fields=("external_reference",))
    name = "Updated voucher"
    variables = {
        "externalReference": voucher.external_reference,
        "input": {"name": name, **reference_input},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_VOUCHER_BY_EXTERNAL_REFERENCE,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    data = get_graphql_content(response)["data"]["voucherUpdate"]
    assert data["errors"] == []
    assert data["voucher"] == {"name": name, "externalReference": expected_reference}
    voucher.refresh_from_db(fields=("name", "external_reference"))
    assert voucher.name == name
    assert voucher.external_reference == expected_reference


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


def test_update_voucher_usage_limit_voucher_already_used(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    checkout,
):
    # given
    assert voucher.usage_limit is None
    code_instance = voucher.codes.first()
    checkout.voucher_code = code_instance.code
    checkout.save(update_fields=["voucher_code"])

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"usageLimit": 10},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["voucherUpdate"]["voucher"]
    errors = content["data"]["voucherUpdate"]["errors"]
    assert len(errors) == 1

    voucher.refresh_from_db()
    assert voucher.usage_limit is None
    assert errors[0]["field"] == "usageLimit"
    assert errors[0]["code"] == DiscountErrorCode.VOUCHER_ALREADY_USED.name


def test_update_voucher_usage_limit_the_same_value(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    checkout,
):
    # given
    usage_limit = 10
    voucher.usage_limit = usage_limit
    voucher.save(update_fields=["usage_limit"])

    code_instance = voucher.codes.first()
    checkout.voucher_code = code_instance.code
    checkout.save(update_fields=["voucher_code"])

    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"usageLimit": usage_limit},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["voucherUpdate"]["errors"]
    assert content["data"]["voucherUpdate"]["voucher"]


def test_update_voucher_with_deprecated_code_field(
    staff_api_client,
    voucher,
    permission_manage_discounts,
):
    # given
    new_code = "new-code"
    code_instance = voucher.codes.get()
    assert code_instance.code != new_code
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {
            "code": new_code,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    assert not content["data"]["voucherUpdate"]["errors"]
    data = content["data"]["voucherUpdate"]["voucher"]
    assert len(data["codes"]["edges"]) == 1
    assert data["codes"]["edges"][0]["node"]["code"] == new_code

    code_instance.refresh_from_db()
    assert code_instance.code == new_code


def test_update_voucher_usage_limit_order_with_given_voucher_code_exists(
    staff_api_client,
    voucher,
    permission_manage_discounts,
    order,
):
    """Ensure the voucher limit can be updated when the order has the same voucher code.

    The voucher usage limit should be updated if an order contains a voucher code that
    matches an existing order’s voucher code, but the voucher associated with
    this code no longer exists.
    """
    # given
    assert voucher.usage_limit is None
    code_instance = voucher.codes.first()

    # set the voucher code for the order, but left the voucher field empty,
    # it simulates the situation when the voucher was deleted, and this code was the
    # part of the different voucher
    order.voucher_code = code_instance.code
    order.voucher = None
    order.save(update_fields=["voucher_code", "voucher"])

    usage_limit = 10
    variables = {
        "id": graphene.Node.to_global_id("Voucher", voucher.id),
        "input": {"usageLimit": usage_limit},
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_VOUCHER_MUTATION, variables, permissions=[permission_manage_discounts]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["voucherUpdate"]["errors"]
    assert not errors
    assert content["data"]["voucherUpdate"]["voucher"]["usageLimit"] == usage_limit
