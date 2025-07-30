import graphene
import pytest

from ......attribute import AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCTS_FILTER_QUERY, PRODUCTS_WHERE_QUERY


@pytest.mark.parametrize("query", [PRODUCTS_WHERE_QUERY, PRODUCTS_FILTER_QUERY])
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
def test_products_query_with_attribute_value_boolean(
    query,
    boolean_input,
    staff_api_client,
    product_type,
    product_list,
    boolean_attribute,
    channel_USD,
):
    # given
    boolean_attribute.slug = "b_s"
    boolean_attribute.type = "PRODUCT_TYPE"
    boolean_attribute.save()

    second_attribute = Attribute.objects.create(
        slug="s_boolean",
        name="Boolean",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.BOOLEAN,
    )

    product_type.product_attributes.set([boolean_attribute, second_attribute])

    true_value = boolean_attribute.values.filter(boolean=True).first()
    true_value.name = "True-name"
    true_value.slug = "true_slug"
    true_value.save()

    associate_attribute_values_to_instance(
        product_list[0], {boolean_attribute.pk: [true_value]}
    )

    value_for_second_attr = AttributeValue.objects.create(
        attribute=second_attribute,
        name=f"{second_attribute.name}: Yes",
        slug=f"{second_attribute.id}_false",
        boolean=False,
    )
    associate_attribute_values_to_instance(
        product_list[1], {second_attribute.pk: [value_for_second_attr]}
    )

    variables = {"where": {"attributes": [boolean_input]}, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
    )

    # then
    content = get_graphql_content(response)
    products_nodes = content["data"]["products"]["edges"]
    assert len(products_nodes) == 1
    assert products_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "Product", product_list[0].pk
    )
