import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....shipping.error_codes import ShippingErrorCode
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....core.enums import WeightUnitsEnum
from ....tests.utils import get_graphql_content
from ...types import PostalCodeRuleInclusionTypeEnum, ShippingMethodTypeEnum

UPDATE_SHIPPING_PRICE_MUTATION = """
    mutation updateShippingPrice(
        $id: ID!,
        $shippingZone: ID!,
        $description: JSONString,
        $type: ShippingMethodTypeEnum!,
        $maximumDeliveryDays: Int,
        $minimumDeliveryDays: Int,
        $maximumOrderWeight: WeightScalar,
        $minimumOrderWeight: WeightScalar,
        $addPostalCodeRules: [ShippingPostalCodeRulesCreateInputRange!],
        $deletePostalCodeRules: [ID!],
        $inclusionType: PostalCodeRuleInclusionTypeEnum,
    ) {
        shippingPriceUpdate(
            id: $id, input: {
                shippingZone: $shippingZone,
                type: $type,
                description: $description,
                maximumDeliveryDays: $maximumDeliveryDays,
                minimumDeliveryDays: $minimumDeliveryDays,
                minimumOrderWeight:$minimumOrderWeight,
                maximumOrderWeight: $maximumOrderWeight,
                addPostalCodeRules: $addPostalCodeRules,
                deletePostalCodeRules: $deletePostalCodeRules,
                inclusionType: $inclusionType,
            }) {
            errors {
                field
                code
            }
            shippingZone {
                id
            }
            shippingMethod {
                description
                type
                minimumDeliveryDays
                maximumDeliveryDays
                postalCodeRules {
                    start
                    end
                }
            }
        }
    }
"""


def test_update_shipping_method(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = 8
    min_del_days = 2
    description = dummy_editorjs("description", True)
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "description": description,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    assert data["shippingZone"]["id"] == shipping_zone_id
    assert data["shippingMethod"]["description"] == description
    assert data["shippingMethod"]["minimumDeliveryDays"] == min_del_days
    assert data["shippingMethod"]["maximumDeliveryDays"] == max_del_days


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_update_shipping_method_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = 8
    min_del_days = 2
    description = dummy_editorjs("description", True)
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "description": description,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }

    # when
    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)

    # then
    data = content["data"]["shippingPriceUpdate"]
    assert not data["errors"]

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": shipping_method_id,
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.SHIPPING_PRICE_UPDATED,
        [any_webhook],
        shipping_method,
        SimpleLazyObject(lambda: staff_api_client.user),
    )


def test_update_shipping_method_postal_codes(
    staff_api_client,
    shipping_method_excluded_by_postal_code,
    permission_manage_shipping,
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_zone_id = graphene.Node.to_global_id(
        "ShippingZone", shipping_method_excluded_by_postal_code.shipping_zone.pk
    )
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method_excluded_by_postal_code.pk
    )
    postal_code_rule_id = graphene.Node.to_global_id(
        "ShippingMethodPostalCodeRule",
        shipping_method_excluded_by_postal_code.postal_code_rules.first().id,
    )
    number_of_postal_code_rules = (
        shipping_method_excluded_by_postal_code.postal_code_rules.count()
    )
    max_del_days = 8
    min_del_days = 2
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "deletePostalCodeRules": [postal_code_rule_id],
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    assert (
        len(data["shippingMethod"]["postalCodeRules"])
        == number_of_postal_code_rules - 1
    )


def test_update_shipping_method_minimum_delivery_days_higher_than_maximum(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = 2
    min_del_days = 8
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_update_shipping_method_minimum_delivery_days_below_0(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = 2
    min_del_days = -1
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_update_shipping_method_maximum_delivery_days_below_0(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = -1
    min_del_days = 10
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "maximumDeliveryDays"


def test_update_shipping_method_minimum_delivery_days_higher_than_max_from_instance(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.maximum_delivery_days = 5
    shipping_method.save(update_fields=["maximum_delivery_days"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    min_del_days = 8
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_update_shipping_method_maximum_delivery_days_lower_than_min_from_instance(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.minimum_delivery_days = 10
    shipping_method.save(update_fields=["minimum_delivery_days"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = 5
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "maximumDeliveryDays"


def test_update_shipping_method_multiple_errors(
    staff_api_client, shipping_zone, permission_manage_shipping
):
    query = UPDATE_SHIPPING_PRICE_MUTATION
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_method.minimum_delivery_days = 10
    shipping_method.save(update_fields=["minimum_delivery_days"])
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    max_del_days = 5
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumOrderWeight": {"value": -2, "unit": WeightUnitsEnum.KG.name},
        "maximumOrderWeight": {"value": -1, "unit": WeightUnitsEnum.KG.name},
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceUpdate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 3
    expected_errors = [
        {"code": ShippingErrorCode.INVALID.name, "field": "maximumDeliveryDays"},
        {"code": ShippingErrorCode.INVALID.name, "field": "minimumOrderWeight"},
        {"code": ShippingErrorCode.INVALID.name, "field": "maximumOrderWeight"},
    ]
    for error in expected_errors:
        assert error in errors


@pytest.mark.parametrize(
    "min_delivery_days, max_delivery_days",
    [
        (None, 1),
        (1, None),
        (None, None),
    ],
)
def test_update_shipping_method_delivery_days_without_value(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
    min_delivery_days,
    max_delivery_days,
):
    shipping_method = shipping_zone.shipping_methods.first()
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    shipping_method_id = graphene.Node.to_global_id(
        "ShippingMethodType", shipping_method.pk
    )
    variables = {
        "shippingZone": shipping_zone_id,
        "id": shipping_method_id,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "minimumDeliveryDays": min_delivery_days,
        "maximumDeliveryDays": max_delivery_days,
        "addPostalCodeRules": [],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }

    response = staff_api_client.post_graphql(
        UPDATE_SHIPPING_PRICE_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    shipping_method.refresh_from_db()

    assert not content["data"]["shippingPriceUpdate"]["errors"]
    assert shipping_method.minimum_delivery_days == min_delivery_days
    assert shipping_method.maximum_delivery_days == max_delivery_days
