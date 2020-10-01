import graphene

from ....product import AttributeInputType
from ....product.error_codes import ProductErrorCode
from ..utils import (
    validate_attributes_input_for_product,
    validate_attributes_input_for_variant,
)


def test_validate_attributes_input_for_product(weight_attribute, color_attribute):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [(weight_attribute, ["a"]), (color_attribute, ["b"])]

    # when
    errors = validate_attributes_input_for_product(input_data)

    # then
    assert not errors


def test_validate_attributes_input_for_product_no_values_given(
    weight_attribute, color_attribute
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [(weight_attribute, []), (color_attribute, [])]

    # when
    errors = validate_attributes_input_for_product(input_data)

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_product_too_many_values_given(
    weight_attribute, color_attribute
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [(weight_attribute, ["abc", "efg"]), (color_attribute, ["a", "b"])]

    # when
    errors = validate_attributes_input_for_product(input_data)

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert error.params["attributes"] == [
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    ]


def test_validate_attributes_input_for_product_empty_values_given(
    weight_attribute, color_attribute
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [(weight_attribute, ["a", None]), (color_attribute, ["  "])]

    # when
    errors = validate_attributes_input_for_product(input_data)

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_product_multiply_errors(
    weight_attribute, color_attribute
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [(weight_attribute, [None]), (color_attribute, ["a", "b"])]

    # when
    errors = validate_attributes_input_for_product(input_data)

    # then
    assert len(errors) == 2
    assert {error.code for error in errors} == {
        ProductErrorCode.INVALID.value,
        ProductErrorCode.REQUIRED.value,
    }
    assert {attr for error in errors for attr in error.params["attributes"]} == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_variant(weight_attribute, color_attribute):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [(weight_attribute, ["a"]), (color_attribute, ["b"])]

    # when
    errors = validate_attributes_input_for_variant(input_data)

    # then
    assert not errors


def test_validate_attributes_input_for_variant_no_values_given(
    weight_attribute, color_attribute
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [(weight_attribute, []), (color_attribute, [])]

    # when
    errors = validate_attributes_input_for_variant(input_data)

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_variant_too_many_values_given(
    weight_attribute, color_attribute
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [(weight_attribute, ["abc", "efg"]), (color_attribute, ["a", "b"])]

    # when
    errors = validate_attributes_input_for_variant(input_data)

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_variant_empty_values_given(
    weight_attribute, color_attribute
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [(weight_attribute, [None]), (color_attribute, ["  "])]

    # when
    errors = validate_attributes_input_for_variant(input_data)

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_variant_multiply_errors(
    weight_attribute, color_attribute
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [(weight_attribute, [None]), (color_attribute, ["a", "b"])]

    # when
    errors = validate_attributes_input_for_variant(input_data)

    # then
    assert len(errors) == 2
    assert {error.code for error in errors} == {
        ProductErrorCode.INVALID.value,
        ProductErrorCode.REQUIRED.value,
    }
    assert {attr for error in errors for attr in error.params["attributes"]} == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }
