import pytest

from ...product.models import ProductType
from ..utils import associate_attribute_values_to_instance


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


def test_associate_attribute_to_product_instance_multiple_values(
    product, attribute_value_generator
):
    """Ensure multiple values in proper order are assigned."""
    old_assignment = product.attributes.first()
    assert old_assignment is not None, "The product doesn't have attribute-values"
    assert old_assignment.values.count() == 1

    attribute = old_assignment.attribute
    attribute_value_generator(
        attribute=attribute,
        slug="attr-value2",
    )
    values = attribute.values.all()

    # Assign new values
    new_assignment = associate_attribute_values_to_instance(
        product, attribute, values[1], values[0]
    )

    # Ensure the new assignment was created and ordered correctly
    assert new_assignment.pk == old_assignment.pk
    assert new_assignment.values.count() == 2
    assert list(
        new_assignment.productvalueassignment.values_list("value_id", "sort_order")
    ) == [(values[1].pk, 0), (values[0].pk, 1)]


def test_associate_attribute_to_page_instance_multiple_values(page):
    """Ensure multiple values in proper order are assigned."""
    old_assignment = page.attributes.first()
    assert old_assignment is not None, "The page doesn't have attribute-values"
    assert old_assignment.values.count() == 1

    attribute = old_assignment.attribute
    values = attribute.values.all()

    # Clear the values
    new_assignment = associate_attribute_values_to_instance(
        page, attribute, values[1], values[0]
    )

    # Ensure the new assignment was created and ordered correctly
    assert new_assignment.pk == old_assignment.pk
    assert new_assignment.values.count() == 2
    assert list(
        new_assignment.pagevalueassignment.values_list("value_id", "sort_order")
    ) == [(values[1].pk, 0), (values[0].pk, 1)]


def test_associate_attribute_to_variant_instance_multiple_values(
    variant, attribute_value_generator
):
    """Ensure multiple values in proper order are assigned."""

    attribute = variant.product.product_type.variant_attributes.first()
    attribute_value_generator(
        attribute=attribute,
        slug="attr-value2",
    )
    values = attribute.values.all()

    new_assignment = associate_attribute_values_to_instance(
        variant, attribute, values[0], values[1]
    )

    # Ensure the new assignment was created and ordered correctly
    assert new_assignment.values.count() == 2
    assert list(
        new_assignment.variantvalueassignment.values_list("value_id", "sort_order")
    ) == [(values[0].pk, 0), (values[1].pk, 1)]


def test_associate_attribute_to_product_copies_data_over_to_new_field(
    product, color_attribute
):
    """Ensure data is double writed.

    Part of implementation of the #12881 issue. We need to check that the
    value of AssignedProductAttribute.product is copied over to
    AssignedProductAttributeValue.product.
    """
    values = color_attribute.values.all()

    # Assign new values
    new_assignment = associate_attribute_values_to_instance(
        product, color_attribute, values[0], values[1]
    )

    # Ensure the new assignment was created
    assert new_assignment.values.count() == 2
    assert list(
        new_assignment.productvalueassignment.values_list("value_id", "product_id")
    ) == [(values[0].pk, product.id), (values[1].pk, product.id)]
