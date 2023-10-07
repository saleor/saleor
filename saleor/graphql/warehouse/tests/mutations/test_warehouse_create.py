import json
from unittest.mock import patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject

from .....account.models import Address
from .....core.utils.json_serializer import CustomJsonEncoder
from .....warehouse.error_codes import WarehouseErrorCode
from .....warehouse.models import Warehouse
from .....webhook.event_types import WebhookEventAsyncType
from ....tests.utils import get_graphql_content

MUTATION_CREATE_WAREHOUSE = """
mutation createWarehouse($input: WarehouseCreateInput!) {
    createWarehouse(input: $input){
        warehouse {
            id
            name
            slug
            companyName
            externalReference
            address {
                id
                metadata {
                    key
                    value
                }
            }
            shippingZones(first: 5) {
                edges {
                    node {
                        id
                    }
                }
            }
        }
        errors {
            message
            field
            code
        }
    }
}
"""


def test_mutation_create_warehouse(
    staff_api_client, permission_manage_products, shipping_zone
):
    # given
    metadata = [{"key": "public", "value": "public_value"}]
    variables = {
        "input": {
            "name": "Test warehouse",
            "slug": "test-warhouse",
            "email": "test-admin@example.com",
            "externalReference": "test-ext-ref",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
                "companyName": "Amazing Company Inc",
                "metadata": metadata,
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    assert Warehouse.objects.count() == 1
    warehouse = Warehouse.objects.first()
    address = warehouse.address
    created_warehouse = content["data"]["createWarehouse"]["warehouse"]
    assert created_warehouse["id"] == graphene.Node.to_global_id(
        "Warehouse", warehouse.id
    )
    assert created_warehouse["name"] == warehouse.name
    assert created_warehouse["slug"] == warehouse.slug
    assert created_warehouse["companyName"] == warehouse.address.company_name
    assert created_warehouse["externalReference"] == warehouse.external_reference
    assert created_warehouse["address"]["metadata"] == metadata
    assert address.metadata == {"public": "public_value"}


def test_mutation_create_warehouse_shipping_zone_provided(
    staff_api_client, permission_manage_products, shipping_zone
):
    # given
    variables = {
        "input": {
            "name": "Test warehouse",
            "slug": "test-warhouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
                "companyName": "Amazing Company Inc",
            },
            # DEPRECATED
            "shippingZones": [
                graphene.Node.to_global_id("ShippingZone", shipping_zone.id)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createWarehouse"]
    errors = data["errors"]
    assert len(errors) == 1
    assert errors[0]["code"] == WarehouseErrorCode.INVALID.name
    assert errors[0]["field"] == "shippingZones"


@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_mutation_create_warehouse_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    permission_manage_products,
    shipping_zone,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    variables = {
        "input": {
            "name": "Test warehouse",
            "slug": "test-warhouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
                "companyName": "Amazing Company Inc",
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    warehouse = Warehouse.objects.last()

    # then
    assert content["data"]["createWarehouse"]["warehouse"]
    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Warehouse", warehouse.id),
                "name": warehouse.name,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.WAREHOUSE_CREATED,
        [any_webhook],
        warehouse,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_mutation_create_warehouse_does_not_create_when_name_is_empty_string(
    staff_api_client, permission_manage_products, shipping_zone
):
    # given
    variables = {
        "input": {
            "name": "  ",
            "slug": "test-warhouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
                "companyName": "Amazing Company Inc",
            },
            "shippingZones": [
                graphene.Node.to_global_id("ShippingZone", shipping_zone.id)
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createWarehouse"]
    errors = data["errors"]
    assert Warehouse.objects.count() == 0
    assert len(errors) == 1
    assert errors[0]["field"] == "name"
    assert errors[0]["code"] == WarehouseErrorCode.REQUIRED.name


def test_create_warehouse_creates_address(
    staff_api_client, permission_manage_products, shipping_zone
):
    # given
    variables = {
        "input": {
            "name": "Test warehouse",
            "email": "test-admin@example.com",
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "companyName": "Amazing Company Inc",
                "postalCode": "53-601",
            },
        }
    }
    assert not Address.objects.exists()

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )

    # then
    content = get_graphql_content(response)
    errors = content["data"]["createWarehouse"]["errors"]
    assert len(errors) == 0
    assert Address.objects.count() == 1
    address = Address.objects.get(street_address_1="Teczowa 8", city="WROCLAW")
    address_id = graphene.Node.to_global_id("Address", address.id)
    warehouse_data = content["data"]["createWarehouse"]["warehouse"]
    assert warehouse_data["address"]["id"] == address_id
    assert address.street_address_1 == "Teczowa 8"
    assert address.company_name == "Amazing Company Inc"
    assert address.city == "WROCLAW"


@pytest.mark.parametrize(
    "input_slug, expected_slug",
    (
        ("test-slug", "test-slug"),
        (None, "test-warehouse"),
        ("", "test-warehouse"),
    ),
)
def test_create_warehouse_with_given_slug(
    staff_api_client, permission_manage_products, input_slug, expected_slug
):
    # given
    query = MUTATION_CREATE_WAREHOUSE
    name = "Test warehouse"
    variables = {"name": name, "slug": input_slug}
    variables = {
        "input": {
            "name": name,
            "slug": input_slug,
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["createWarehouse"]
    assert not data["errors"]
    assert data["warehouse"]["slug"] == expected_slug


def test_create_warehouse_with_non_unique_external_reference(
    staff_api_client, permission_manage_products, shipping_zone, warehouse
):
    # given
    ext_ref = "test-ext-ref"
    warehouse.external_reference = ext_ref
    warehouse.save(update_fields=["external_reference"])

    variables = {
        "input": {
            "name": "Test warehouse",
            "externalReference": ext_ref,
            "address": {
                "streetAddress1": "Teczowa 8",
                "city": "Wroclaw",
                "country": "PL",
                "postalCode": "53-601",
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(
        MUTATION_CREATE_WAREHOUSE,
        variables=variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)

    # then
    error = content["data"]["createWarehouse"]["errors"][0]
    assert error["field"] == "externalReference"
    assert error["code"] == WarehouseErrorCode.UNIQUE.name
    assert error["message"] == "Warehouse with this External reference already exists."
