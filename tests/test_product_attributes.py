from unittest.mock import MagicMock, Mock

import pytest
from prices import Money

from saleor.product import AttributeInputType
from saleor.product.models import AttributeValue, Product, ProductType, ProductVariant
from saleor.product.tasks import _update_variants_names
from saleor.product.utils.attributes import (
    associate_attribute_values_to_instance,
    generate_name_for_variant,
)


@pytest.fixture()
def variant_with_no_attributes(category):
    """Create a variant having no attributes, the same for the parent product."""
    product_type = ProductType.objects.create(
        name="Test product type", has_variants=True, is_shipping_required=True
    )
    product = Product.objects.create(
        name="Test product",
        price=Money(10, "USD"),
        product_type=product_type,
        category=category,
    )
    variant = ProductVariant.objects.create(product=product, sku="123")
    return variant


def test_generate_name_for_variant(
    variant_with_no_attributes, color_attribute_without_values, size_attribute
):
    """Test the name generation from a given variant containing multiple attributes and
    different input types (dropdown and multiselect).
    """

    variant = variant_with_no_attributes
    color_attribute = color_attribute_without_values

    # Assign the attributes to the product type
    variant.product.product_type.variant_attributes.set(
        (color_attribute, size_attribute)
    )

    # Set the color attribute to a multi-value attribute
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["input_type"])

    # Create colors
    colors = AttributeValue.objects.bulk_create(
        [
            AttributeValue(attribute=color_attribute, name="Yellow", slug="yellow"),
            AttributeValue(attribute=color_attribute, name="Blue", slug="blue"),
            AttributeValue(attribute=color_attribute, name="Red", slug="red"),
        ]
    )

    # Retrieve the size attribute value "Big"
    size = size_attribute.values.get(slug="big")

    # Associate the colors and size to variant attributes
    associate_attribute_values_to_instance(variant, color_attribute, *tuple(colors))
    associate_attribute_values_to_instance(variant, size_attribute, size)

    # Generate the variant name from the attributes
    name = generate_name_for_variant(variant)
    assert name == "Yellow, Blue, Red / Big"


def test_generate_name_from_values_empty(variant_with_no_attributes):
    """Ensure generate a variant name from a variant without any attributes assigned
    returns an empty string."""
    name = generate_name_for_variant(variant_with_no_attributes)
    assert name == ""


def test_product_type_update_changes_variant_name(product):
    new_name = "test_name"
    product_variant = product.variants.first()
    assert not product_variant.name == new_name
    attribute = product.product_type.variant_attributes.first()
    attribute_value = attribute.values.first()
    attribute_value.name = new_name
    attribute_value.save()
    _update_variants_names(product.product_type, [attribute])
    product_variant.refresh_from_db()
    assert product_variant.name == new_name


def test_update_variants_changed_does_nothing_with_no_attributes():
    product_type = MagicMock(spec=ProductType)
    product_type.variant_attributes.all = Mock(return_value=[])
    saved_attributes = []
    # FIXME: This method no longer returns any value
    assert _update_variants_names(product_type, saved_attributes) is None


def test_associate_attribute_to_non_product_instance(color_attribute):
    instance = ProductType()
    attribute = color_attribute
    value = color_attribute.values.first()

    with pytest.raises(AssertionError) as exc:
        associate_attribute_values_to_instance(instance, attribute, value)  # noqa

    assert exc.value.args == ("ProductType is unsupported",)


def test_associate_attribute_to_product_instance_from_different_attribute(
    product, color_attribute, size_attribute
):
    """Ensure an assertion error is raised when one tries to associate attribute values
    to an object that don't belong to the supplied attribute.
    """
    instance = product
    attribute = color_attribute
    value = size_attribute.values.first()

    with pytest.raises(AssertionError) as exc:
        associate_attribute_values_to_instance(instance, attribute, value)

    assert exc.value.args == ("Some values are not from the provided attribute.",)


def test_associate_attribute_to_product_instance_without_values(product):
    """Ensure clearing the values from a product is properly working."""
    old_assignment = product.attributes.first()
    assert old_assignment is not None, "The product doesn't have attribute-values"
    assert old_assignment.values.count() == 1

    attribute = old_assignment.attribute

    # Clear the values
    new_assignment = associate_attribute_values_to_instance(product, attribute)

    # Ensure the values were cleared and no new assignment entry was created
    assert new_assignment.pk == old_assignment.pk
    assert new_assignment.values.count() == 0
