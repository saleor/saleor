import datetime
import json
from unittest.mock import call, patch

import graphene
import pytest
from django.utils import timezone
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....discount import DiscountValueType, VoucherType
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Voucher
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import (
    assert_no_permission,
    get_graphql_content,
    get_graphql_content_from_response,
)
from ...enums import DiscountValueTypeEnum, VoucherTypeEnum
from ...mutations.voucher.catalogue_validation import VOUCHER_CATALOGUE_ITEMS_LIMIT

CREATE_VOUCHER_WITH_EXTERNAL_REFERENCE_MUTATION = """
    mutation createVoucher($name: String, $externalReference: String) {
        voucherCreate(
            input: {
                name: $name
                addCodes: [""]
                externalReference: $externalReference
            }
        ) {
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


@pytest.mark.parametrize(
    ("_case", "external_reference"),
    [
        ("non_empty", "test-ext-ref"),
        ("empty_string", ""),
    ],
)
def test_with_external_reference(
    _case, external_reference, staff_api_client, permission_manage_discounts
):
    # given
    name = "test-voucher"
    variables = {"name": name, "externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherCreate"]
    assert data["errors"] == []
    assert data["voucher"]["externalReference"] == external_reference
    voucher = Voucher.objects.get(name=name)
    assert voucher.external_reference == external_reference


@pytest.mark.parametrize(
    ("_case", "external_reference"),
    [
        ("non_empty", "test-ext-ref"),
        ("empty_string", ""),
    ],
)
def test_with_non_unique_external_reference(
    _case, external_reference, staff_api_client, voucher, permission_manage_discounts
):
    # given
    voucher.external_reference = external_reference
    voucher.save(update_fields=["external_reference"])

    name = "new-voucher"
    variables = {"name": name, "externalReference": external_reference}

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["voucherCreate"]
    assert data["voucher"] is None
    assert Voucher.objects.filter(name=name).exists() is False
    errors = data["errors"]
    assert len(errors) == 1
    assert (
        errors[0]["message"] == "Voucher with this External reference already exists."
    )
    assert errors[0]["field"] == "externalReference"
    assert errors[0]["code"] == DiscountErrorCode.UNIQUE.name


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
    permission_manage_discounts,
    mocker,
):
    # given
    client = request.getfixturevalue(client_fixture)
    name = "Changed voucher"
    webhook = mocker.patch("saleor.plugins.manager.PluginsManager.voucher_created")
    variables = {"name": name, "externalReference": "new-reference"}

    # when
    response = client.post_graphql(
        CREATE_VOUCHER_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts] if is_allowed else [],
        check_no_permissions=False,
    )

    # then
    if is_allowed:
        data = get_graphql_content(response)["data"]["voucherCreate"]
        assert data["errors"] == []
        created = Voucher.objects.get(external_reference="new-reference")
        assert created.name == name
        assert data["voucher"] == {
            "name": name,
            "externalReference": created.external_reference,
        }
        webhook.assert_called_once()
    else:
        assert_no_permission(response)
        content = get_graphql_content_from_response(response)
        assert content["data"] == {"voucherCreate": None}
        assert len(content["errors"]) == 1
        assert content["errors"][0]["path"] == ["voucherCreate"]
        assert content["errors"][0]["message"] == (
            "To access this path, you need one of the following permissions: MANAGE_DISCOUNTS"
        )
        assert Voucher.objects.filter(name=name).exists() is False
        webhook.assert_not_called()


@pytest.mark.parametrize(
    ("_case", "reference_input"),
    [("omitted", {}), ("null", {"externalReference": None})],
)
def test_without_external_reference(
    _case,
    reference_input,
    staff_api_client,
    permission_manage_discounts,
):
    # given
    name = "Voucher without reference"
    variables = {"name": name, **reference_input}

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_EXTERNAL_REFERENCE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    data = get_graphql_content(response)["data"]["voucherCreate"]
    assert data["errors"] == []
    assert data["voucher"] == {"name": name, "externalReference": None}
    created = Voucher.objects.get(name=name)
    assert created.external_reference is None


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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)

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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)

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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)

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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)

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

    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)

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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)
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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)
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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)
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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)
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
    start_date = timezone.now() - datetime.timedelta(days=365)
    end_date = timezone.now() + datetime.timedelta(days=365)
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
    start_date = timezone.now() + datetime.timedelta(days=365)
    end_date = timezone.now() - datetime.timedelta(days=365)

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


CREATE_VOUCHER_WITH_CATALOGUE_MUTATION = """
    mutation voucherCreate($input: VoucherInput!) {
        voucherCreate(input: $input) {
            voucher {
                productTypes(first: 10) { edges { node { id } } }
                excludedProducts(first: 10) { edges { node { id } } }
                excludedVariants(first: 10) { edges { node { id } } }
                excludedCollections(first: 10) { edges { node { id } } }
                excludedCategories(first: 10) { edges { node { id } } }
                excludedProductTypes(first: 10) { edges { node { id } } }
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def _connection_ids(connection):
    return [edge["node"]["id"] for edge in connection["edges"]]


def test_with_catalogue_exclusions(
    staff_api_client,
    permission_manage_discounts,
    product,
    variant,
    collection,
    category,
    product_type_list,
):
    # given
    name = "Everything but fees"
    product_type_id = graphene.Node.to_global_id("ProductType", product_type_list[0].pk)
    excluded_product_type_id = graphene.Node.to_global_id(
        "ProductType", product_type_list[1].pk
    )
    product_id = graphene.Node.to_global_id("Product", product.pk)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    collection_id = graphene.Node.to_global_id("Collection", collection.pk)
    category_id = graphene.Node.to_global_id("Category", category.pk)
    variables = {
        "input": {
            "name": name,
            "addCodes": ["FEES-EXCLUDED"],
            "type": VoucherTypeEnum.SPECIFIC_PRODUCT.name,
            "productTypes": [product_type_id],
            "excludedProducts": [product_id],
            "excludedVariants": [variant_id],
            "excludedCollections": [collection_id],
            "excludedCategories": [category_id],
            "excludedProductTypes": [excluded_product_type_id],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    assert data["errors"] == []
    voucher_data = data["voucher"]
    assert _connection_ids(voucher_data["productTypes"]) == [product_type_id]
    assert _connection_ids(voucher_data["excludedProducts"]) == [product_id]
    assert _connection_ids(voucher_data["excludedVariants"]) == [variant_id]
    assert _connection_ids(voucher_data["excludedCollections"]) == [collection_id]
    assert _connection_ids(voucher_data["excludedCategories"]) == [category_id]
    assert _connection_ids(voucher_data["excludedProductTypes"]) == [
        excluded_product_type_id
    ]
    voucher = Voucher.objects.get(name=name)
    assert list(voucher.product_types.all()) == [product_type_list[0]]
    assert list(voucher.excluded_products.all()) == [product]
    assert list(voucher.excluded_variants.all()) == [variant]
    assert list(voucher.excluded_collections.all()) == [collection]
    assert list(voucher.excluded_categories.all()) == [category]
    assert list(voucher.excluded_product_types.all()) == [product_type_list[1]]


@pytest.mark.parametrize(
    ("_case", "voucher_type"),
    [
        ("entire_order", VoucherTypeEnum.ENTIRE_ORDER),
        ("shipping", VoucherTypeEnum.SHIPPING),
    ],
)
def test_exclusions_rejected_for_non_specific_product_type(
    _case, voucher_type, staff_api_client, permission_manage_discounts, product_type
):
    # given
    name = "Order voucher"
    variables = {
        "input": {
            "name": name,
            "addCodes": ["ORDER-VOUCHER"],
            "type": voucher_type.name,
            "excludedProductTypes": [
                graphene.Node.to_global_id("ProductType", product_type.pk)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    assert data["voucher"] is None
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "excludedProductTypes"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["message"] == (
        "Exclusions are supported only by vouchers of type SPECIFIC_PRODUCT."
    )
    assert Voucher.objects.filter(name=name).exists() is False


@pytest.mark.parametrize(
    ("_case", "type_name", "included_field", "excluded_field", "fixture_name"),
    [
        ("product", "Product", "products", "excludedProducts", "product"),
        ("variant", "ProductVariant", "variants", "excludedVariants", "variant"),
        (
            "collection",
            "Collection",
            "collections",
            "excludedCollections",
            "collection",
        ),
        ("category", "Category", "categories", "excludedCategories", "category"),
        (
            "product_type",
            "ProductType",
            "productTypes",
            "excludedProductTypes",
            "product_type",
        ),
    ],
)
def test_same_item_included_and_excluded(
    _case,
    type_name,
    included_field,
    excluded_field,
    fixture_name,
    request,
    staff_api_client,
    permission_manage_discounts,
):
    # given
    name = "Conflicting voucher"
    item_id = graphene.Node.to_global_id(
        type_name, request.getfixturevalue(fixture_name).pk
    )
    variables = {
        "input": {
            "name": name,
            "addCodes": ["CONFLICT"],
            "type": VoucherTypeEnum.SPECIFIC_PRODUCT.name,
            included_field: [item_id],
            excluded_field: [item_id],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    assert data["voucher"] is None
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == excluded_field
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["message"] == (
        f"Cannot both include and exclude the same items: {item_id}. "
        f"Remove them from `{included_field}` or `{excluded_field}` first."
    )
    assert Voucher.objects.filter(name=name).exists() is False


def test_exclusions_over_limit(staff_api_client, permission_manage_discounts):
    # given
    name = "Too many exclusions"
    variables = {
        "input": {
            "name": name,
            "addCodes": ["TOO-MANY"],
            "type": VoucherTypeEnum.SPECIFIC_PRODUCT.name,
            "excludedProducts": [
                graphene.Node.to_global_id("Product", -pk)
                for pk in range(1, VOUCHER_CATALOGUE_ITEMS_LIMIT + 2)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        CREATE_VOUCHER_WITH_CATALOGUE_MUTATION,
        variables,
        permissions=[permission_manage_discounts],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["voucherCreate"]
    assert data["voucher"] is None
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["field"] == "excludedProducts"
    assert errors[0]["code"] == DiscountErrorCode.INVALID.name
    assert errors[0]["message"] == (
        f"Cannot provide more than {VOUCHER_CATALOGUE_ITEMS_LIMIT} items."
    )
    assert Voucher.objects.filter(name=name).exists() is False
