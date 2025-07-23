import graphene
import pytest

from ......attribute import AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import QUERY_PAGES_WITH_WHERE


@pytest.mark.parametrize(
    "boolean_input",
    [
        {"value": {"boolean": True}},
        {"value": {"name": {"eq": "True-name"}}},
        {"value": {"slug": {"eq": "true_slug"}}},
        {"value": {"name": {"oneOf": ["True-name", "True-name-2"]}}},
        {"value": {"slug": {"oneOf": ["true_slug"]}}},
        {"slug": "b_s", "value": {"boolean": True}},
        {"slug": "b_s", "value": {"name": {"eq": "True-name"}}},
        {"slug": "b_s", "value": {"slug": {"eq": "true_slug"}}},
        {"slug": "b_s", "value": {"name": {"oneOf": ["True-name", "True-name-2"]}}},
        {"slug": "b_s", "value": {"slug": {"oneOf": ["true_slug"]}}},
    ],
)
def test_pages_query_with_attribute_value_boolean(
    boolean_input,
    staff_api_client,
    page_list,
    page_type,
    boolean_attribute,
):
    # given
    boolean_attribute.slug = "b_s"
    boolean_attribute.type = "PAGE_TYPE"
    boolean_attribute.save()

    second_attribute = Attribute.objects.create(
        slug="s_boolean",
        name="Boolean",
        type=AttributeType.PAGE_TYPE,
        input_type=AttributeInputType.BOOLEAN,
    )

    page_type.page_attributes.add(boolean_attribute)
    page_type.page_attributes.add(second_attribute)

    true_value = boolean_attribute.values.filter(boolean=True).first()
    true_value.name = "True-name"
    true_value.slug = "true_slug"
    true_value.save()

    associate_attribute_values_to_instance(
        page_list[0], {boolean_attribute.pk: [true_value]}
    )

    value_for_second_attr = AttributeValue.objects.create(
        attribute=second_attribute,
        name=f"{second_attribute.name}: Yes",
        slug=f"{second_attribute.id}_false",
        boolean=False,
    )
    associate_attribute_values_to_instance(
        page_list[1], {second_attribute.pk: [value_for_second_attr]}
    )

    variables = {"where": {"attributes": [boolean_input]}}

    # when
    response = staff_api_client.post_graphql(
        QUERY_PAGES_WITH_WHERE,
        variables,
    )

    # then
    content = get_graphql_content(response)
    pages_nodes = content["data"]["pages"]["edges"]
    assert len(pages_nodes) == 1
    assert pages_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Page", page_list[0].pk
    )
