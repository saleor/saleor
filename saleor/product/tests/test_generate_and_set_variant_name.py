from unittest.mock import MagicMock, Mock

from ...attribute import AttributeInputType
from ...attribute.models import AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ..models import ProductType
from ..tasks import _update_variants_names
from ..utils.variants import generate_and_set_variant_name


def test_generate_and_set_variant_name_different_attributes(
    variant_with_no_attributes, color_attribute_without_values, size_attribute
):
    """Test variant name generation with a mix of (non-)selection attributes."""

    variant = variant_with_no_attributes
    color_attribute = color_attribute_without_values

    # Assign the attributes to the product type
    variant.product.product_type.variant_attributes.add(
        size_attribute, through_defaults={"variant_selection": True}
    )
    variant.product.product_type.variant_attributes.add(color_attribute)

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
    associate_attribute_values_to_instance(
        variant,
        {
            color_attribute.id: colors,
            size_attribute.id: [size],
        },
    )

    # Generate the variant name from the attributes
    generate_and_set_variant_name(variant, variant.sku)
    variant.refresh_from_db()
    assert variant.name == "Big"


def test_generate_and_set_variant_name_only_variant_selection_attributes(
    variant_with_no_attributes, color_attribute_without_values, size_attribute
):
    """Test that selection attributes properly affect variant name generation."""

    variant = variant_with_no_attributes
    color_attribute = color_attribute_without_values

    # Assign the attributes to the product type
    variant.product.product_type.variant_attributes.set(
        (color_attribute, size_attribute), through_defaults={"variant_selection": True}
    )

    # Create values
    colors = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=color_attribute, name="Yellow", slug="yellow", sort_order=1
            ),
            AttributeValue(
                attribute=color_attribute, name="Blue", slug="blue", sort_order=2
            ),
            AttributeValue(
                attribute=color_attribute, name="Red", slug="red", sort_order=3
            ),
        ]
    )

    # Retrieve the size attribute value "Big"
    size = size_attribute.values.get(slug="big")
    size.sort_order = 4
    size.save(update_fields=["sort_order"])

    # Associate the colors and size to variant attributes
    associate_attribute_values_to_instance(
        variant,
        {
            color_attribute.id: colors,
            size_attribute.id: [size],
        },
    )

    # Generate the variant name from the attributes
    generate_and_set_variant_name(variant, variant.sku)
    variant.refresh_from_db()
    assert variant.name == "Big / Yellow, Blue, Red"


def test_generate_and_set_variant_name_only_not_variant_selection_attributes(
    variant_with_no_attributes, color_attribute_without_values, file_attribute
):
    """Test that non-selection attributes don't affect variant name generation."""

    variant = variant_with_no_attributes
    color_attribute = color_attribute_without_values

    # Assign the attributes to the product type
    variant.product.product_type.variant_attributes.set(
        (color_attribute, file_attribute)
    )

    # Set the color attribute to a multi-value attribute
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["input_type"])

    # Create values
    values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(attribute=color_attribute, name="Yellow", slug="yellow"),
            AttributeValue(attribute=color_attribute, name="Blue", slug="blue"),
            AttributeValue(
                attribute=file_attribute,
                name="test_file_3.txt",
                slug="test_file3txt",
                file_url="https://example.com/test_media/test_file3.txt",
                content_type="text/plain",
            ),
        ]
    )

    # Associate the colors and size to variant attributes
    associate_attribute_values_to_instance(
        variant,
        {
            color_attribute.id: values[:2],
            file_attribute.id: [values[-1]],
        },
    )

    # Generate the variant name from the attributes
    generate_and_set_variant_name(variant, variant.sku)
    variant.refresh_from_db()
    assert variant.name == variant.sku


def test_generate_name_from_values_empty(variant_with_no_attributes):
    """Ensure a variant name generated from no attributes is an empty string."""
    variant = variant_with_no_attributes
    generate_and_set_variant_name(variant, variant.sku)
    variant.refresh_from_db()
    assert variant.name == variant.sku


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


def test_only_not_variant_selection_attr_left_variant_name_change_to_sku(product):
    new_name = "test_name"
    product_variant = product.variants.first()
    assert not product_variant.name == new_name
    attribute = product.product_type.variant_attributes.first()
    variant_attribute = attribute.attributevariant.get()
    variant_attribute.variant_selection = False
    variant_attribute.save(update_fields=["variant_selection"])

    attribute.input_type = AttributeInputType.MULTISELECT
    attribute.save(update_fields=["input_type"])
    _update_variants_names(product.product_type, [attribute])
    product_variant.refresh_from_db()
    assert product_variant.name == product_variant.sku


def test_update_variants_changed_does_nothing_with_no_attributes():
    product_type = MagicMock(spec=ProductType)
    product_type.variant_attributes.all = Mock(return_value=[])
    saved_attributes = []
    # FIXME: This method no longer returns any value
    assert _update_variants_names(product_type, saved_attributes) is None


def test_only_not_variant_selection_attr_left_variant_name_change_to_global_id(product):
    new_name = "test_name"
    product_variant = product.variants.first()
    assert not product_variant.name == new_name
    product_variant.sku = None
    product_variant.save()
    attribute = product.product_type.variant_attributes.first()
    attribute.input_type = AttributeInputType.MULTISELECT
    variant_attribute = attribute.attributevariant.get()
    variant_attribute.variant_selection = False
    variant_attribute.save(update_fields=["variant_selection"])

    attribute.save(update_fields=["input_type"])
    _update_variants_names(product.product_type, [attribute])
    product_variant.refresh_from_db()
    assert product_variant.name == product_variant.get_global_id()
