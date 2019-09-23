import json

import pytest

from saleor.product import AttributeInputType
from saleor.product.models import Attribute, AttributeValue
from saleor.product.utils.attributes import associate_attribute_values_to_instance
from saleor.seo.schema.email import (
    get_order_confirmation_markup,
    get_organization,
    get_product_data,
)
from saleor.seo.schema.product import get_brand_from_attributes


def test_get_organization(site_settings):
    example_name = "Saleor Brand Name"
    site = site_settings.site
    site.name = example_name
    site.save()

    result = get_organization()
    assert result["name"] == example_name


def test_get_product_data_without_image(order_with_lines):
    """Tested OrderLine Product has no image assigned."""
    line = order_with_lines.lines.first()
    organization = get_organization()
    result = get_product_data(line, organization)
    assert "image" not in result["itemOffered"]


def test_get_product_data_with_image(order_with_lines, product_with_image):
    line = order_with_lines.lines.first()
    variant = product_with_image.variants.first()
    line.variant = variant
    line.product_name = str(variant.product)
    line.variant_name = str(variant)
    line.save()
    organization = get_organization()
    result = get_product_data(line, organization)
    assert "image" in result["itemOffered"]
    assert result["itemOffered"]["name"] == variant.display_product()


def test_get_order_confirmation_markup(order_with_lines):
    try:
        result = get_order_confirmation_markup(order_with_lines)
    except TypeError:
        pytest.fail("Function output is not JSON serializable")

    try:
        # Response should be returned as a valid json
        json.loads(result)
    except ValueError:
        pytest.fail("Response is not a valid json")


def test_get_brand_from_attributes(product):
    attribute = Attribute.objects.create(
        slug="brand", name="Brand", input_type=AttributeInputType.MULTISELECT
    )
    product.product_type.product_attributes.add(attribute)

    # Set the brand attribute as a multi-value attribute
    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])

    # Add some brands names
    brands = AttributeValue.objects.bulk_create(
        [
            AttributeValue(attribute=attribute, name="Saleor", slug="saleor"),
            AttributeValue(attribute=attribute, name="Mirumee", slug="mirumee"),
        ]
    )

    # Associate the brand names to the product
    associate_attribute_values_to_instance(product, attribute, *tuple(brands))

    # Retrieve the brand names from the product attributes
    brand_names_str = get_brand_from_attributes(product.attributes)
    assert brand_names_str == "Saleor, Mirumee"


def test_get_brand_from_attributes_no_brand_associated(product):
    # Retrieve the brand names from the product attributes
    brand_names_str = get_brand_from_attributes(product.attributes)
    assert brand_names_str is None
