import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject

from .....core.utils.json_serializer import CustomJsonEncoder
from .....warehouse import WarehouseClickAndCollectOption
from .....warehouse.error_codes import WarehouseErrorCode
from .....warehouse.models import Warehouse
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content
from ...enums import WarehouseClickAndCollectOptionEnum

MUTATION_UPDATE_WAREHOUSE = """
mutation updateWarehouse($input: WarehouseUpdateInput!, $id: ID!) {
    updateWarehouse(id: $id, input: $input) {
        errors {
            message
            field
            code
        }
        warehouse {
            name
            slug
            companyName
            isPrivate
            clickAndCollectOption
            externalReference
            address {
                id
                streetAddress1
                streetAddress2
                postalCode
                metadata {
                    key
                    value
                }
            }
        }
    }
}
"""


def test_mutation_update_warehouse(
    staff_api_client, warehouse, permission_manage_products, graphql_address_data
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    warehouse_old_name = warehouse.name
    warehouse_slug = warehouse.slug
    external_reference = "test-ext-ref"
    variables = {
        "id": warehouse_id,
        "input": {
            "name": "New name",
            "externalReference": external_reference,
            "address": graphql_address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    warehouse.refresh_from_db()
    warehouse_data = content["data"]["updateWarehouse"]["warehouse"]

    assert warehouse_data["address"]["metadata"] == [
        {"key": "public", "value": "public_value"}
    ]
    assert warehouse.address.metadata == {"public": "public_value"}
    assert warehouse.address.validation_skipped is False
    assert not (warehouse.name == warehouse_old_name)
    assert warehouse.name == "New name"
    assert warehouse.slug == warehouse_slug
    assert warehouse.external_reference == external_reference


def test_mutation_update_warehouse_with_non_unique_external_reference(
    staff_api_client, warehouse, permission_manage_products, warehouse_JPY
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    ext_ref = "test-ext-ref"
    warehouse_JPY.external_reference = ext_ref
    warehouse_JPY.save(update_fields=["external_reference"])

    variables = {
        "id": warehouse_id,
        "input": {"externalReference": ext_ref},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["updateWarehouse"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == WarehouseErrorCode.UNIQUE.name
    assert error["message"] == "Warehouse with this External reference already exists."


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_mutation_update_warehouse_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    warehouse,
    permission_manage_products,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {
        "id": warehouse_id,
        "input": {"name": "New name"},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    warehouse.refresh_from_db()

    # then
    assert content["data"]["updateWarehouse"]["warehouse"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": variables["id"],
                "name": warehouse.name,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.WAREHOUSE_UPDATED,
        [any_webhook],
        warehouse,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_mutation_update_warehouse_can_update_address(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    address_id = graphene.Node.to_global_id("Address", warehouse.address.pk)
    address = warehouse.address
    variables = {
        "id": warehouse_id,
        "input": {
            "name": warehouse.name,
            "address": {
                "streetAddress1": "Teczowa 8",
                "streetAddress2": "Ground floor",
                "companyName": "",
                "city": address.city,
                "country": address.country.code,
                "postalCode": "53-601",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    content_address = content["data"]["updateWarehouse"]["warehouse"]["address"]
    assert content_address["id"] == address_id
    address.refresh_from_db()
    assert address.street_address_1 == "Teczowa 8"
    assert address.street_address_2 == "Ground floor"


def test_mutation_update_warehouse_to_country_with_different_validation_rules(
    staff_api_client, warehouse, permission_manage_products, address_usa
):
    # given
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)
    warehouse.address = address_usa
    warehouse.save(update_fields=["address"])
    address_id = graphene.Node.to_global_id("Address", warehouse.address.pk)
    variables = {
        "id": warehouse_id,
        "input": {
            "name": warehouse.name,
            "address": {
                "streetAddress1": "Fake street",
                "city": "London",
                "country": "GB",
                "postalCode": "B52 1AA",
            },
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    content_address = content["data"]["updateWarehouse"]["warehouse"]["address"]

    # then
    assert len(content["data"]["updateWarehouse"]["errors"]) == 0
    assert content_address["streetAddress1"] == "Fake street"
    assert content_address["id"] == address_id


@pytest.mark.parametrize(
    ("input_slug", "expected_slug", "error_message"),
    [
        ("test-slug", "test-slug", None),
        ("", "", "Slug value cannot be blank."),
        (None, "", "Slug value cannot be blank."),
    ],
)
def test_update_warehouse_slug(
    staff_api_client,
    warehouse,
    permission_manage_products,
    input_slug,
    expected_slug,
    error_message,
):
    # given
    query = MUTATION_UPDATE_WAREHOUSE
    old_slug = warehouse.slug

    assert old_slug != input_slug

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": node_id, "input": {"slug": input_slug}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]
    if not error_message:
        assert not errors
        assert data["warehouse"]["slug"] == expected_slug
    else:
        assert errors
        assert errors[0]["field"] == "slug"
        assert errors[0]["code"] == WarehouseErrorCode.REQUIRED.name


def test_update_warehouse_slug_exists(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    query = MUTATION_UPDATE_WAREHOUSE
    input_slug = "test-slug"

    second_warehouse = Warehouse.objects.get(pk=warehouse.pk)
    second_warehouse.pk = None
    second_warehouse.slug = input_slug
    second_warehouse.save()

    assert input_slug != warehouse.slug

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"id": node_id, "input": {"slug": input_slug}}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]
    assert errors
    assert errors[0]["field"] == "slug"
    assert errors[0]["code"] == WarehouseErrorCode.UNIQUE.name


@pytest.mark.parametrize(
    (
        "input_slug",
        "expected_slug",
        "input_name",
        "expected_name",
        "error_message",
        "error_field",
    ),
    [
        ("test-slug", "test-slug", "New name", "New name", None, None),
        (
            "test-slug",
            "test-slug",
            " stripped ",
            "stripped",
            None,
            None,
        ),
        ("", "", "New name", "New name", "Slug value cannot be blank.", "slug"),
        (None, "", "New name", "New name", "Slug value cannot be blank.", "slug"),
        ("test-slug", "", None, None, "This field cannot be blank.", "name"),
        ("test-slug", "", "", None, "This field cannot be blank.", "name"),
        (None, None, None, None, "Slug value cannot be blank.", "slug"),
        ("test-slug", "test-slug", "  ", None, "Name value cannot be blank", "name"),
    ],
)
def test_update_warehouse_slug_and_name(
    staff_api_client,
    warehouse,
    permission_manage_products,
    input_slug,
    expected_slug,
    input_name,
    expected_name,
    error_message,
    error_field,
):
    # given
    query = MUTATION_UPDATE_WAREHOUSE

    old_name = warehouse.name
    old_slug = warehouse.slug

    assert input_slug != old_slug
    assert input_name != old_name

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {"input": {"slug": input_slug, "name": input_name}, "id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]
    if not error_message:
        assert data["warehouse"]["name"] == expected_name == warehouse.name
        assert (
            data["warehouse"]["slug"] == input_slug == warehouse.slug == expected_slug
        )
    else:
        assert errors
        assert errors[0]["field"] == error_field
        assert errors[0]["code"] == WarehouseErrorCode.REQUIRED.name


@pytest.mark.parametrize(
    ("expected_private", "expected_cc_option"),
    [
        (private, option)
        for private in (True, False)
        for option in [
            WarehouseClickAndCollectOptionEnum.ALL.name,
            WarehouseClickAndCollectOptionEnum.DISABLED.name,
        ]
    ]
    + [(False, WarehouseClickAndCollectOptionEnum.LOCAL.name)],
)
def test_update_click_and_collect_option(
    staff_api_client,
    warehouse,
    permission_manage_products,
    expected_private,
    expected_cc_option,
):
    # given
    query = MUTATION_UPDATE_WAREHOUSE

    assert warehouse.is_private
    assert warehouse.click_and_collect_option == WarehouseClickAndCollectOption.DISABLED

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {
        "input": {
            "isPrivate": expected_private,
            "clickAndCollectOption": expected_cc_option,
        },
        "id": node_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]

    assert not errors
    assert data["warehouse"]["isPrivate"] == expected_private == warehouse.is_private
    assert (
        data["warehouse"]["clickAndCollectOption"]
        == expected_cc_option
        == warehouse.click_and_collect_option.upper()
    )


def test_update_click_and_collect_option_invalid_input(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    query = MUTATION_UPDATE_WAREHOUSE

    warehouse_is_private = warehouse.is_private
    warehouse_click_and_collect = warehouse.click_and_collect_option
    assert warehouse_is_private
    assert warehouse_click_and_collect == WarehouseClickAndCollectOption.DISABLED

    node_id = graphene.Node.to_global_id("Warehouse", warehouse.id)
    variables = {
        "input": {
            "isPrivate": True,
            "clickAndCollectOption": WarehouseClickAndCollectOptionEnum.LOCAL.name,
        },
        "id": node_id,
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]
    errors = data["errors"]

    assert len(errors) == 1
    assert (
        errors[0]["message"]
        == "Local warehouse can be toggled only for non-private warehouse stocks"
    )
    assert errors[0]["field"] == "clickAndCollectOption"

    assert warehouse.is_private == warehouse_is_private
    assert warehouse.click_and_collect_option == warehouse_click_and_collect


MUTATION_UPDATE_WAREHOUSE_BY_EXTERNAL_REFERENCE = """
    mutation updateWarehouse($input: WarehouseUpdateInput!,
            $id: ID, $externalReference: String) {
    updateWarehouse(id: $id, input: $input, externalReference: $externalReference) {
    errors {
      message
      field
      code
    }
    warehouse {
      name
      slug
      externalReference
    }
  }
}
"""


def test_mutation_update_warehouse_by_external_reference(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    external_reference = "test-ext-ref"
    warehouse.external_reference = external_reference
    warehouse.save(update_fields=["external_reference"])
    variables = {
        "externalReference": external_reference,
        "input": {
            "name": "New name",
            "externalReference": external_reference,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    warehouse.refresh_from_db()
    data = content["data"]["updateWarehouse"]["warehouse"]
    assert data["name"] == "New name"
    assert warehouse.name == "New name"
    assert warehouse.external_reference == external_reference


def test_update_warehouse_by_both_id_and_external_reference(
    staff_api_client, warehouse, permission_manage_products
):
    # given
    external_reference = "test-ext-ref"
    warehouse.external_reference = external_reference
    warehouse.save(update_fields=["external_reference"])
    variables = {
        "externalReference": external_reference,
        "id": warehouse.id,
        "input": {"name": "New name"},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["updateWarehouse"]
    # then
    assert data["errors"]
    assert (
        data["errors"][0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_update_product_external_reference_not_existing(
    staff_api_client, permission_manage_products
):
    # given
    external_reference = "non-existing-ext-ref"
    variables = {
        "externalReference": external_reference,
        "input": {},
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE_BY_EXTERNAL_REFERENCE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    data = content["data"]["updateWarehouse"]

    # then
    assert data["errors"]
    assert (
        data["errors"][0]["message"]
        == f"Couldn't resolve to a node: {external_reference}"
    )


def test_update_warehouse_invalid_address_skip_validation(
    staff_api_client,
    warehouse,
    permission_manage_products,
    graphql_address_data_skipped_validation,
):
    # given
    address_data = graphql_address_data_skipped_validation
    invalid_postal_code = "invalid_postal_code"
    address_data["postalCode"] = invalid_postal_code
    warehouse_id = graphene.Node.to_global_id("Warehouse", warehouse.pk)

    variables = {
        "id": warehouse_id,
        "input": {
            "name": warehouse.name,
            "address": address_data,
        },
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_UPDATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["updateWarehouse"]
    assert not data["errors"]
    assert data["warehouse"]["address"]["postalCode"] == invalid_postal_code
    warehouse.refresh_from_db()
    assert warehouse.address.postal_code == invalid_postal_code
    assert warehouse.address.validation_skipped is True
