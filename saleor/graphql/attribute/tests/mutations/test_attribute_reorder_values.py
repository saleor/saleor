import json
from unittest import mock

import graphene
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time

from .....attribute.models import AttributeValue
from .....core.utils.json_serializer import CustomJsonEncoder
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.payloads import generate_meta, generate_requestor
from ....tests.utils import get_graphql_content

ATTRIBUTE_VALUES_REORDER_MUTATION = """
    mutation attributeReorderValues($attributeId: ID!, $moves: [ReorderInput!]!) {
        attributeReorderValues(attributeId: $attributeId, moves: $moves) {
            attribute {
                id
                choices(first: 10) {
                    edges {
                        node {
                            id
                        }
                    }
                }
            }

    errors {
        field
        message
        }
    }
}
"""


def test_sort_values_within_attribute_invalid_product_type(
    staff_api_client, permission_manage_product_types_and_attributes
):
    """Try to reorder an invalid attribute (invalid ID)."""

    attribute_id = graphene.Node.to_global_id("Attribute", -1)
    value_id = graphene.Node.to_global_id("AttributeValue", -1)

    variables = {
        "attributeId": attribute_id,
        "moves": [{"id": value_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTE_VALUES_REORDER_MUTATION,
            variables,
            permissions=[permission_manage_product_types_and_attributes],
        )
    )["data"]["attributeReorderValues"]

    assert content["errors"] == [
        {
            "field": "attributeId",
            "message": f"Couldn't resolve to an attribute: {attribute_id}",
        }
    ]


def test_sort_values_within_attribute_invalid_id(
    staff_api_client, permission_manage_product_types_and_attributes, color_attribute
):
    """Try to reorder a value not associated to the given attribute."""

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    value_id = graphene.Node.to_global_id("AttributeValue", -1)

    variables = {
        "type": "VARIANT",
        "attributeId": attribute_id,
        "moves": [{"id": value_id, "sortOrder": 1}],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(
            ATTRIBUTE_VALUES_REORDER_MUTATION,
            variables,
            permissions=[permission_manage_product_types_and_attributes],
        )
    )["data"]["attributeReorderValues"]

    assert content["errors"] == [
        {
            "field": "moves",
            "message": f"Couldn't resolve to an attribute value: {value_id}",
        }
    ]


def test_sort_values_within_attribute(
    staff_api_client, color_attribute, permission_manage_product_types_and_attributes
):
    attribute = color_attribute
    AttributeValue.objects.create(attribute=attribute, name="Green", slug="green")
    values = list(attribute.values.all())
    assert len(values) == 3

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    attribute_id = graphene.Node.to_global_id("Attribute", attribute.id)
    m2m_values = attribute.values
    m2m_values.set(values)

    assert values == sorted(
        values, key=lambda o: o.sort_order if o.sort_order is not None else o.pk
    ), "The values are not properly ordered"

    variables = {
        "attributeId": attribute_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", values[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("AttributeValue", values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    expected_order = [values[1].pk, values[2].pk, values[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTE_VALUES_REORDER_MUTATION, variables)
    )["data"]["attributeReorderValues"]
    assert not content["errors"]

    assert content["attribute"]["id"] == attribute_id

    gql_values = content["attribute"]["choices"]["edges"]
    assert len(gql_values) == len(expected_order)

    actual_order = []

    for attr, expected_pk in zip(gql_values, expected_order):
        gql_type, gql_attr_id = graphene.Node.from_global_id(attr["node"]["id"])
        assert gql_type == "AttributeValue"
        actual_order.append(int(gql_attr_id))

    assert actual_order == expected_order


@freeze_time("2022-05-12 12:00:00")
@mock.patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@mock.patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
def test_sort_values_trigger_webhook(
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    color_attribute,
    permission_manage_product_types_and_attributes,
    settings,
):
    # given
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    AttributeValue.objects.create(attribute=color_attribute, name="Green", slug="green")
    values = list(color_attribute.values.all())
    assert len(values) == 3

    staff_api_client.user.user_permissions.add(
        permission_manage_product_types_and_attributes
    )

    attribute_id = graphene.Node.to_global_id("Attribute", color_attribute.id)
    m2m_values = color_attribute.values
    m2m_values.set(values)

    assert values == sorted(
        values, key=lambda o: o.sort_order if o.sort_order is not None else o.pk
    ), "The values are not properly ordered"

    variables = {
        "attributeId": attribute_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", values[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("AttributeValue", values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(ATTRIBUTE_VALUES_REORDER_MUTATION, variables)
    )["data"]["attributeReorderValues"]
    meta = generate_meta(
        requestor_data=generate_requestor(
            SimpleLazyObject(lambda: staff_api_client.user)
        )
    )

    attribute_updated_call = mock.call(
        json.dumps(
            {
                "id": graphene.Node.to_global_id("Attribute", color_attribute.id),
                "name": color_attribute.name,
                "slug": color_attribute.slug,
                "meta": meta,
            },
            cls=CustomJsonEncoder,
        ),
        WebhookEventAsyncType.ATTRIBUTE_UPDATED,
        [any_webhook],
        color_attribute,
        SimpleLazyObject(lambda: staff_api_client.user),
    )

    def generate_attribute_value_update_call(value):
        return mock.call(
            json.dumps(
                {
                    "id": graphene.Node.to_global_id("AttributeValue", value.id),
                    "name": value.name,
                    "slug": value.slug,
                    "value": value.value,
                    "meta": meta,
                },
                cls=CustomJsonEncoder,
            ),
            WebhookEventAsyncType.ATTRIBUTE_VALUE_UPDATED,
            [any_webhook],
            value,
            SimpleLazyObject(lambda: staff_api_client.user),
        )

    attribute_value_1_updated_call = generate_attribute_value_update_call(values[0])
    attribute_value_2_updated_call = generate_attribute_value_update_call(values[2])
    # then
    assert not content["errors"]
    assert content["attribute"]["id"] == attribute_id
    assert len(mocked_webhook_trigger.call_args_list) == 3
    assert attribute_updated_call in mocked_webhook_trigger.call_args_list
    assert attribute_value_1_updated_call in mocked_webhook_trigger.call_args_list
    assert attribute_value_2_updated_call in mocked_webhook_trigger.call_args_list
