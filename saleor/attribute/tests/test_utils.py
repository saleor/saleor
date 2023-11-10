import pytest

from ...attribute.models import AssignedPageAttributeValue
from ...product.models import ProductType
from ..utils import (
    associate_attribute_values_to_instance,
)
from .model_helpers import (
    get_page_attribute_values,
    get_page_attributes,
    get_product_attribute_values,
    get_product_attributes,
)


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
    instance = product
    attribute = color_attribute
    value = size_attribute.values.first()

    with pytest.raises(AssertionError) as exc:
        associate_attribute_values_to_instance(instance, attribute, value)

    assert exc.value.args == ("Some values are not from the provided attribute.",)


def test_associate_attribute_to_product_instance_without_values(product):
    """Ensure clearing the values from a product is properly working."""
    attribute = get_product_attributes(product).first()
    assert attribute is not None, "Product doesn't have attributes assigned"
    value_count = get_product_attribute_values(product, attribute).count()
    assert value_count == 1, "Product doesn't have attribute-values"

    # Clear the values
    associate_attribute_values_to_instance(product, attribute)

    # Ensure the values were cleared and no new assignment entry was created
    assert get_product_attributes(product).count() == 1
    assert product.attributevalues.count() == 0


def test_disassociate_attributes_from_instance(product):
    """Ensure clearing the values from a product is properly working."""
    attribute = get_product_attributes(product).first()
    assert attribute is not None, "Product doesn't have attributes assigned"
    value_count = get_product_attribute_values(product, attribute).count()
    assert value_count == 1, "Product doesn't have attribute-values"

    # This should clear the values
    associate_attribute_values_to_instance(product, attribute)

    # Check that the attribute still belongs to the product but doesn't have values
    attribute = get_product_attributes(product).first()
    assert attribute is not None, "Product doesn't have attributes assigned"
    value_count = get_product_attribute_values(product, attribute).count()
    assert value_count == 0, "Product has attribute-values assigned after removal"


def test_associate_attribute_to_product_instance_multiple_values(
    product, attribute_value_generator
):
    """Ensure multiple values in proper order are assigned."""
    attribute = get_product_attributes(product).first()
    assert attribute is not None, "Product doesn't have attributes assigned"
    value_count = get_product_attribute_values(product, attribute).count()
    assert value_count == 1, "Product doesn't have attribute-values"

    attribute_value_generator(
        attribute=attribute,
        slug="attr-value2",
    )
    values = attribute.values.all()

    # Assign new values
    associate_attribute_values_to_instance(product, attribute, values[1], values[0])

    # Ensure the new assignment was created and ordered correctly
    assert product.attributevalues.count() == 2
    assert list(product.attributevalues.values_list("value_id", "sort_order")) == [
        (values[1].pk, 0),
        (values[0].pk, 1),
    ]


def test_associate_attribute_to_page_instance_multiple_values(page):
    """Ensure multiple values in proper order are assigned."""
    attribute = get_page_attributes(page).first()
    assert attribute is not None, "The page doesn't have attribute-values"
    assert get_page_attribute_values(page, attribute).count() == 1

    values = attribute.values.all()

    # Clear the values
    associate_attribute_values_to_instance(page, attribute, values[1], values[0])

    # Ensure the new assignment was created and ordered correctly
    assigned_values = (
        AssignedPageAttributeValue.objects.filter(
            page_id=page.pk, value__attribute_id=attribute.id
        )
        .prefetch_related("value")
        .order_by("sort_order")
    )
    assert len(assigned_values) == 2
    assert assigned_values[0].value == values[1]
    assert assigned_values[0].sort_order == 0
    assert assigned_values[1].value == values[0]
    assert assigned_values[1].sort_order == 1


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
    associate_attribute_values_to_instance(
        product, color_attribute, values[0], values[1]
    )

    # Ensure the new assignment was created
    assert product.attributevalues.count() == 2
    assert list(product.attributevalues.values_list("value_id", "product_id")) == [
        (values[0].pk, product.id),
        (values[1].pk, product.id),
    ]
