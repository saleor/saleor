import graphene

from .....attribute.models import AttributeValue
from ....tests.utils import get_graphql_content

ATTRIBUTE_VALUES_REORDER_MUTATION = """
    mutation attributeReorderValues($attributeId: ID!, $moves: [ReorderInput]!) {
      attributeReorderValues(attributeId: $attributeId, moves: $moves) {
        attribute {
          id
          values {
            id
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

    gql_values = content["attribute"]["values"]
    assert len(gql_values) == len(expected_order)

    actual_order = []

    for attr, expected_pk in zip(gql_values, expected_order):
        gql_type, gql_attr_id = graphene.Node.from_global_id(attr["id"])
        assert gql_type == "AttributeValue"
        actual_order.append(int(gql_attr_id))

    assert actual_order == expected_order
