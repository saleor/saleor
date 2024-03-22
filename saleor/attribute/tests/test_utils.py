import pytest

from ...product.models import ProductType
from ..utils import associate_attribute_values_to_instance


def test_associate_attribute_to_non_product_instance(color_attribute):
    instance = ProductType()
    attribute = color_attribute
    value = color_attribute.values.first()

    with pytest.raises(AssertionError) as exc:
        associate_attribute_values_to_instance(
            instance,
            {attribute.id: [value]},
        )  # noqa

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
        associate_attribute_values_to_instance(
            instance,
            {attribute.id: [value]},
        )

    assert exc.value.args == ("Some values are not from the provided attribute.",)


def test_associate_attribute_to_product_instance_without_values(product):
    """Ensure clearing the values from a product is properly working."""
    old_assignment = product.attributes.first()
    assert old_assignment is not None, "The product doesn't have attribute-values"
    assert old_assignment.values.count() == 1

    attribute = old_assignment.attribute

    # Clear the values
    associate_attribute_values_to_instance(product, {attribute.id: []})
    new_assignment = product.attributes.last()

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
    associate_attribute_values_to_instance(
        product, {attribute.id: [values[1], values[0]]}
    )
    new_assignment = product.attributes.last()

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
    associate_attribute_values_to_instance(page, {attribute.id: [values[1], values[0]]})
    new_assignment = page.attributes.last()

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

    associate_attribute_values_to_instance(
        variant, {attribute.id: [values[0], values[1]]}
    )

    new_assignment = variant.attributes.last()
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
    associate_attribute_values_to_instance(
        product, {color_attribute.id: [values[0], values[1]]}
    )
    new_assignment = product.attributes.last()

    # Ensure the new assignment was created
    assert new_assignment.values.count() == 2
    assert list(
        new_assignment.productvalueassignment.values_list("value_id", "product_id")
    ) == [(values[0].pk, product.id), (values[1].pk, product.id)]


def test_associate_attribute_to_instance_duplicated_values(
    product, attribute_value_generator, multiselect_attribute, color_attribute
):
    # Ensure values are properly assigned even if the new value name is the same
    # as value of different attribute.
    product.product_type.product_attributes.add(multiselect_attribute, color_attribute)
    color_attribute_value = color_attribute.values.first()

    # create multiselect value with the same name as color value
    multiselect_value = attribute_value_generator(
        attribute=multiselect_attribute,
        slug=color_attribute_value.slug,
        name=color_attribute_value.name,
    )
    new_color_value = attribute_value_generator(
        attribute=color_attribute,
        slug="new-color-value",
        name="New color value",
    )

    # Assign new values
    associate_attribute_values_to_instance(
        product,
        {
            color_attribute.id: [new_color_value],
            multiselect_attribute.id: [multiselect_value],
        },
    )

    # Ensure the new assignment was created
    assert product.attributevalues.count() == 2
    assert set(product.attributevalues.values_list("value_id", "product_id")) == {
        (new_color_value.pk, product.id),
        (multiselect_value.pk, product.id),
    }
