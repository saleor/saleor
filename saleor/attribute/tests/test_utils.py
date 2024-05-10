import pytest

from ...attribute.models import AssignedPageAttributeValue
from ...product.models import ProductType
from .. import AttributeInputType, AttributeType
from ..models import Attribute, AttributeValue
from ..utils import (
    associate_attribute_values_to_instance,
    validate_attribute_owns_values,
)
from .model_helpers import (
    get_page_attribute_values,
    get_page_attributes,
    get_product_attribute_values,
    get_product_attributes,
)


@pytest.fixture
def attribute_1():
    attr = Attribute.objects.create(
        slug="attribute-1",
        name="Attribute 1",
        input_type=AttributeInputType.DROPDOWN,
        type=AttributeType.PRODUCT_TYPE,
    )
    AttributeValue.objects.create(
        attribute=attr,
        name="Value 1",
        slug="value-1",
    )
    return attr


@pytest.fixture
def attribute_2():
    attr = Attribute.objects.create(
        slug="attribute-2",
        name="Attribute 2",
        input_type=AttributeInputType.DROPDOWN,
        type=AttributeType.PRODUCT_TYPE,
    )
    AttributeValue.objects.create(
        attribute=attr,
        name="Value 1",
        slug="value-1",
    )
    return attr


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
    attribute = get_product_attributes(product).first()
    assert attribute is not None, "Product doesn't have attributes assigned"
    value_count = get_product_attribute_values(product, attribute).count()
    assert value_count == 1, "Product doesn't have attribute-values"

    # Clear the values
    associate_attribute_values_to_instance(product, {attribute.id: []})

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
    associate_attribute_values_to_instance(product, {attribute.id: []})

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
    associate_attribute_values_to_instance(
        product, {attribute.id: [values[1], values[0]]}
    )

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
    associate_attribute_values_to_instance(page, {attribute.id: [values[1], values[0]]})

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

    # Ensure the new assignment was created
    assert product.attributevalues.count() == 2
    assert list(product.attributevalues.values_list("value_id", "product_id")) == [
        (values[0].pk, product.id),
        (values[1].pk, product.id),
    ]


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


def test_validate_attribute_owns_values(attribute_1, attribute_2):
    # given
    attr_val_map = {
        attribute_1.id: [attribute_1.values.first()],
        attribute_2.id: [attribute_2.values.first()],
    }

    # when
    validate_attribute_owns_values(attr_val_map)

    # then
    assert attr_val_map == {
        attribute_1.id: [attribute_1.values.first()],
        attribute_2.id: [attribute_2.values.first()],
    }
