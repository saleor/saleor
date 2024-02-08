import graphene

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....page.error_codes import PageErrorCode
from ....tests.utils import get_graphql_content

PAGE_REORDER_ATTRIBUTE_VALUES_MUTATION = """
    mutation PageReorderAttributeValues(
      $pageId: ID!
      $attributeId: ID!
      $moves: [ReorderInput!]!
    ) {
      pageReorderAttributeValues(
        pageId: $pageId
        attributeId: $attributeId
        moves: $moves
      ) {
        page {
          id
          attributes {
            attribute {
                id
                slug
            }
            values {
                id
            }
          }
        }

        errors {
          field
          message
          code
          attributes
          values
        }
      }
    }
"""


def test_sort_page_attribute_values(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_page_reference_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    page_type = page.page_type
    page_type.page_attributes.clear()
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_id = graphene.Node.to_global_id("Page", page.id)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.id
    )
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_2",
                name="test name 2",
            ),
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_3",
                name="test name 3",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.id: attr_values}
    )

    variables = {
        "pageId": page_id,
        "attributeId": attribute_id,
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[0].pk),
                "sortOrder": +1,
            },
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[2].pk),
                "sortOrder": -2,
            },
        ],
    }

    expected_order = [attr_values[2].pk, attr_values[1].pk, attr_values[0].pk]

    content = get_graphql_content(
        staff_api_client.post_graphql(PAGE_REORDER_ATTRIBUTE_VALUES_MUTATION, variables)
    )["data"]["pageReorderAttributeValues"]
    assert not content["errors"]

    assert content["page"]["id"] == page_id, "Did not return the correct page"

    gql_attribute_values = content["page"]["attributes"][0]["values"]
    assert len(gql_attribute_values) == 3

    for attr, expected_pk in zip(gql_attribute_values, expected_order):
        db_type, value_pk = graphene.Node.from_global_id(attr["id"])
        assert db_type == "AttributeValue"
        assert int(value_pk) == expected_pk

    apa_values = page.attributevalues.filter(
        value__attribute_id=page_type_page_reference_attribute.id
    )
    assert len(apa_values) == 3


def test_sort_page_attribute_values_invalid_attribute_id(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_page_reference_attribute,
    color_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    page_type = page.page_type
    page_type.page_attributes.clear()
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_id = graphene.Node.to_global_id("Page", page.id)
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_2",
                name="test name 2",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.id: attr_values}
    )

    variables = {
        "pageId": page_id,
        "attributeId": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        "moves": [
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[0].pk),
                "sortOrder": +1,
            },
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(PAGE_REORDER_ATTRIBUTE_VALUES_MUTATION, variables)
    )["data"]["pageReorderAttributeValues"]
    errors = content["errors"]
    assert not content["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "attributeId"


def test_sort_page_attribute_values_invalid_value_id(
    staff_api_client,
    permission_manage_pages,
    page,
    page_type_page_reference_attribute,
    color_attribute,
):
    staff_api_client.user.user_permissions.add(permission_manage_pages)

    page_type = page.page_type
    page_type.page_attributes.clear()
    page_type.page_attributes.add(page_type_page_reference_attribute)

    page_id = graphene.Node.to_global_id("Page", page.id)
    attribute_id = graphene.Node.to_global_id(
        "Attribute", page_type_page_reference_attribute.id
    )
    attr_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_1",
                name="test name 1",
            ),
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_2",
                name="test name 2",
            ),
            AttributeValue(
                attribute=page_type_page_reference_attribute,
                slug=f"{page.pk}_3",
                name="test name 3",
            ),
        ]
    )
    associate_attribute_values_to_instance(
        page, {page_type_page_reference_attribute.id: attr_values}
    )

    invalid_value_id = graphene.Node.to_global_id(
        "AttributeValue", color_attribute.values.first().pk
    )

    variables = {
        "pageId": page_id,
        "attributeId": attribute_id,
        "moves": [
            {"id": invalid_value_id, "sortOrder": +1},
            {
                "id": graphene.Node.to_global_id("AttributeValue", attr_values[2].pk),
                "sortOrder": -1,
            },
        ],
    }

    content = get_graphql_content(
        staff_api_client.post_graphql(PAGE_REORDER_ATTRIBUTE_VALUES_MUTATION, variables)
    )["data"]["pageReorderAttributeValues"]
    errors = content["errors"]
    assert not content["page"]
    assert len(errors) == 1
    assert errors[0]["code"] == PageErrorCode.NOT_FOUND.name
    assert errors[0]["field"] == "moves"
    assert errors[0]["values"] == [invalid_value_id]
