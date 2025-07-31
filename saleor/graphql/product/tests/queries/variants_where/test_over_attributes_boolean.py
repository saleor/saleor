import graphene
import pytest

from ......attribute import AttributeInputType, AttributeType
from ......attribute.models import Attribute, AttributeValue
from ......attribute.utils import associate_attribute_values_to_instance
from .....tests.utils import get_graphql_content
from .shared import PRODUCT_VARIANTS_WHERE_QUERY


@pytest.mark.parametrize(
    "boolean_input",
    [
        {"value": {"boolean": True}},
        {"value": {"name": {"eq": "True-name"}}},
        {"value": {"slug": {"eq": "true_slug"}}},
        {"value": {"name": {"oneOf": ["True-name", "non-existing"]}}},
        {"value": {"slug": {"oneOf": ["true_slug"]}}},
        {"slug": "b_s", "value": {"boolean": True}},
        {"slug": "b_s", "value": {"name": {"eq": "True-name"}}},
        {"slug": "b_s", "value": {"slug": {"eq": "true_slug"}}},
        {"slug": "b_s", "value": {"name": {"oneOf": ["True-name", "non-existing"]}}},
        {"slug": "b_s", "value": {"slug": {"oneOf": ["true_slug"]}}},
    ],
)
def test_product_variants_query_with_attribute_value_boolean(
    boolean_input,
    staff_api_client,
    product_variant_list,
    boolean_attribute,
    channel_USD,
):
    # given
    product = product_variant_list[0].product
    product_type = product.product_type

    boolean_attribute.slug = "b_s"
    boolean_attribute.save()

    second_attribute = Attribute.objects.create(
        slug="s_boolean",
        name="Boolean",
        type=AttributeType.PRODUCT_TYPE,
        input_type=AttributeInputType.BOOLEAN,
    )

    product_type.variant_attributes.add(boolean_attribute, second_attribute)

    true_value = boolean_attribute.values.filter(boolean=True).first()
    true_value.name = "True-name"
    true_value.slug = "true_slug"
    true_value.save()

    variant_1 = product_variant_list[0]
    associate_attribute_values_to_instance(
        variant_1, {boolean_attribute.pk: [true_value]}
    )

    variant_2 = product_variant_list[1]
    value_for_second_attr = AttributeValue.objects.create(
        attribute=second_attribute,
        name=f"{second_attribute.name}: Yes",
        slug=f"{second_attribute.id}_false",
        boolean=False,
    )
    associate_attribute_values_to_instance(
        variant_2, {second_attribute.pk: [value_for_second_attr]}
    )

    variables = {"where": {"attributes": [boolean_input]}, "channel": channel_USD.slug}

    # when
    response = staff_api_client.post_graphql(
        PRODUCT_VARIANTS_WHERE_QUERY,
        variables,
    )

    # then
    content = get_graphql_content(response)
    variants_nodes = content["data"]["productVariants"]["edges"]
    assert len(variants_nodes) == 1
    assert variants_nodes[0]["node"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", variant_1.pk
    )
