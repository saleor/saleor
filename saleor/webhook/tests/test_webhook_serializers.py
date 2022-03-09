from operator import itemgetter
from unittest.mock import ANY

import graphene

from ...attribute.models import AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ..serializers import serialize_product_or_variant_attributes


def test_serialize_product_attributes(
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_type_page_reference_attribute,
    page,
):
    variant_data = serialize_product_or_variant_attributes(
        product_with_variant_with_two_attributes.variants.first()
    )

    product_type = product_with_multiple_values_attributes.product_type
    product_type.product_attributes.add(product_type_page_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        name=page.title,
        slug=f"{product_with_multiple_values_attributes.pk}_{page.pk}",
        reference_page=page,
    )
    associate_attribute_values_to_instance(
        product_with_multiple_values_attributes,
        product_type_page_reference_attribute,
        attr_value,
    )
    product_data = serialize_product_or_variant_attributes(
        product_with_multiple_values_attributes
    )
    assert len(variant_data) == 2
    assert variant_data[1] == {
        "entity_type": None,
        "id": ANY,
        "input_type": "dropdown",
        "name": "Size",
        "slug": "size",
        "unit": None,
        "values": [
            {
                "file": None,
                "name": "Small",
                "reference": None,
                "rich_text": None,
                "date_time": None,
                "date": None,
                "boolean": None,
                "slug": "small",
                "value": "",
            }
        ],
    }

    assert len(product_data) == 2
    assert product_data[0]["name"] == "Available Modes"
    assert sorted(product_data[0]["values"], key=itemgetter("name")) == [
        {
            "name": "Eco Mode",
            "slug": "eco",
            "file": None,
            "reference": None,
            "rich_text": None,
            "date_time": None,
            "date": None,
            "boolean": None,
            "value": "",
        },
        {
            "name": "Performance Mode",
            "slug": "power",
            "file": None,
            "reference": None,
            "rich_text": None,
            "date_time": None,
            "date": None,
            "boolean": None,
            "value": "",
        },
    ]
    assert product_data[1]["name"] == "Page reference"
    assert sorted(product_data[1]["values"], key=itemgetter("name")) == [
        {
            "name": "Test page",
            "slug": attr_value.slug,
            "file": None,
            "reference": graphene.Node.to_global_id(
                attr_value.attribute.entity_type, page.pk
            ),
            "rich_text": None,
            "date_time": None,
            "date": None,
            "boolean": None,
            "value": "",
        },
    ]
