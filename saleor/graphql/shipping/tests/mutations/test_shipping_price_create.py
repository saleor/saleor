import json
from unittest import mock

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....core.utils.json_serializer import CustomJsonEncoder
from .....shipping.error_codes import ShippingErrorCode
from .....shipping.models import ShippingMethod
from .....tests.utils import dummy_editorjs
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....core.enums import WeightUnitsEnum
from ....tests.utils import get_graphql_content
from ...types import PostalCodeRuleInclusionTypeEnum, ShippingMethodTypeEnum

PRICE_BASED_SHIPPING_MUTATION = """
    mutation createShippingPrice(
        $type: ShippingMethodTypeEnum,
        $name: String!,
        $description: JSONString,
        $shippingZone: ID!,
        $maximumDeliveryDays: Int,
        $minimumDeliveryDays: Int,
        $addPostalCodeRules: [ShippingPostalCodeRulesCreateInputRange!]
        $deletePostalCodeRules: [ID!]
        $inclusionType: PostalCodeRuleInclusionTypeEnum
        $taxClass: ID
    ) {
        shippingPriceCreate(
            input: {
                name: $name, shippingZone: $shippingZone, type: $type,
                maximumDeliveryDays: $maximumDeliveryDays,
                minimumDeliveryDays: $minimumDeliveryDays,
                addPostalCodeRules: $addPostalCodeRules,
                deletePostalCodeRules: $deletePostalCodeRules,
                inclusionType: $inclusionType,
                description: $description,
                taxClass: $taxClass
            }) {
            errors {
                field
                code
            }
            shippingZone {
                id
            }
            shippingMethod {
                id
                name
                description
                channelListings {
                    price {
                        amount
                    }
                    minimumOrderPrice {
                        amount
                    }
                    maximumOrderPrice {
                        amount
                    }
                }
                taxClass {
                    id
                }
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


@pytest.mark.parametrize(
    "postal_code_rules",
    [
        [{"start": "HB3", "end": "HB6"}],
        [],
    ],
)
def test_create_shipping_method(
    staff_api_client,
    shipping_zone,
    postal_code_rules,
    permission_manage_shipping,
    tax_classes,
):
    # given
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 10
    min_del_days = 3
    description = dummy_editorjs("description", True)
    tax_class_id = graphene.Node.to_global_id("TaxClass", tax_classes[0].pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "description": description,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": postal_code_rules,
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
        "taxClass": tax_class_id,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["errors"]
    assert not errors
    assert data["shippingMethod"]["name"] == name
    assert data["shippingMethod"]["description"] == description
    assert data["shippingMethod"]["type"] == ShippingMethodTypeEnum.PRICE.name
    assert data["shippingZone"]["id"] == shipping_zone_id
    assert data["shippingMethod"]["minimumDeliveryDays"] == min_del_days
    assert data["shippingMethod"]["maximumDeliveryDays"] == max_del_days
    assert data["shippingMethod"]["postalCodeRules"] == postal_code_rules
    assert data["shippingMethod"]["taxClass"]["id"] == tax_class_id


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_create_shipping_method_trigger_webhook(
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

    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 10
    min_del_days = 3
    description = dummy_editorjs("description", True)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "description": description,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": [{"start": "HB3", "end": "HB6"}],
        "deletePostalCodeRules": [],
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    shipping_method = ShippingMethod.objects.last()

    # then
    errors = data["errors"]
    assert not errors
    assert shipping_method

    mocked_webhook_trigger.assert_called_once_with(
        json.dumps(
            {
                "id": graphene.Node.to_global_id(
                    "ShippingMethodType", shipping_method.id
                ),
                "meta": generate_meta(
                    requestor_data=generate_requestor(
                        SimpleLazyObject(lambda: staff_api_client.user)
                    )
                ),
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.SHIPPING_PRICE_CREATED,
        [any_webhook],
        shipping_method,
        SimpleLazyObject(lambda: staff_api_client.user),
        allow_replica=False,
    )


def test_create_shipping_method_minimum_delivery_days_higher_than_maximum(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    # given
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 3
    min_del_days = 10
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_create_shipping_method_minimum_delivery_days_below_0(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    # given
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 3
    min_del_days = -1
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "minimumDeliveryDays"


def test_create_shipping_method_maximum_delivery_days_below_0(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    # given
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = -1
    min_del_days = 10
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.INVALID.name
    assert errors[0]["field"] == "maximumDeliveryDays"


def test_create_shipping_method_postal_code_duplicate_entry(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    # given
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 10
    min_del_days = 3
    postal_code_rules = [
        {"start": "HB3", "end": "HB6"},
        {"start": "HB3", "end": "HB6"},
    ]
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": postal_code_rules,
        "inclusionType": PostalCodeRuleInclusionTypeEnum.EXCLUDE.name,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.ALREADY_EXISTS.name
    assert errors[0]["field"] == "addPostalCodeRules"


def test_create_shipping_method_postal_code_missing_inclusion_type(
    staff_api_client,
    shipping_zone,
    permission_manage_shipping,
):
    # given
    name = "DHL"
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    max_del_days = 10
    min_del_days = 3
    postal_code_rules = [
        {"start": "HB3", "end": "HB6"},
    ]
    variables = {
        "shippingZone": shipping_zone_id,
        "name": name,
        "type": ShippingMethodTypeEnum.PRICE.name,
        "maximumDeliveryDays": max_del_days,
        "minimumDeliveryDays": min_del_days,
        "addPostalCodeRules": postal_code_rules,
    }

    # when
    response = staff_api_client.post_graphql(
        PRICE_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    errors = data["errors"]
    assert not data["shippingMethod"]
    assert len(errors) == 1
    assert errors[0]["code"] == ShippingErrorCode.REQUIRED.name
    assert errors[0]["field"] == "inclusionType"


WEIGHT_BASED_SHIPPING_MUTATION = """
    mutation createShippingPrice(
        $type: ShippingMethodTypeEnum
        $name: String!
        $shippingZone: ID!
        $maximumOrderWeight: WeightScalar
        $minimumOrderWeight: WeightScalar
        ) {
        shippingPriceCreate(
            input: {
                name: $name,shippingZone: $shippingZone,
                minimumOrderWeight:$minimumOrderWeight,
                maximumOrderWeight: $maximumOrderWeight,
                type: $type
            }) {
            errors {
                field
                code
            }
            shippingMethod {
                minimumOrderWeight {
                    value
                    unit
                }
                maximumOrderWeight {
                    value
                    unit
                }
            }
            shippingZone {
                id
            }
        }
    }
"""


@pytest.mark.parametrize(
    ("min_weight", "max_weight", "expected_min_weight", "expected_max_weight"),
    [
        (
            10.32,
            15.64,
            {"value": 10.32, "unit": WeightUnitsEnum.KG.name},
            {"value": 15.64, "unit": WeightUnitsEnum.KG.name},
        ),
        (10.92, None, {"value": 10.92, "unit": WeightUnitsEnum.KG.name}, None),
    ],
)
def test_create_weight_based_shipping_method(
    shipping_zone,
    staff_api_client,
    min_weight,
    max_weight,
    expected_min_weight,
    expected_max_weight,
    permission_manage_shipping,
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "minimumOrderWeight": min_weight,
        "maximumOrderWeight": max_weight,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }

    # when
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    assert data["shippingMethod"]["minimumOrderWeight"] == expected_min_weight
    assert data["shippingMethod"]["maximumOrderWeight"] == expected_max_weight
    assert data["shippingZone"]["id"] == shipping_zone_id


def test_create_weight_shipping_method_errors(
    shipping_zone, staff_api_client, permission_manage_shipping
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "minimumOrderWeight": 20,
        "maximumOrderWeight": 15,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }

    # when
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    assert data["errors"][0]["code"] == ShippingErrorCode.MAX_LESS_THAN_MIN.name


def test_create_shipping_method_with_negative_min_weight(
    shipping_zone, staff_api_client, permission_manage_shipping
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "minimumOrderWeight": -20,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }

    # when
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    error = data["errors"][0]
    assert error["field"] == "minimumOrderWeight"
    assert error["code"] == ShippingErrorCode.INVALID.name


def test_create_shipping_method_with_negative_max_weight(
    shipping_zone, staff_api_client, permission_manage_shipping
):
    # given
    shipping_zone_id = graphene.Node.to_global_id("ShippingZone", shipping_zone.pk)
    variables = {
        "shippingZone": shipping_zone_id,
        "name": "DHL",
        "maximumOrderWeight": -15,
        "type": ShippingMethodTypeEnum.WEIGHT.name,
    }

    # when
    response = staff_api_client.post_graphql(
        WEIGHT_BASED_SHIPPING_MUTATION,
        variables,
        permissions=[permission_manage_shipping],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["shippingPriceCreate"]
    error = data["errors"][0]
    assert error["field"] == "maximumOrderWeight"
    assert error["code"] == ShippingErrorCode.INVALID.name
