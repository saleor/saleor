import graphene
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from ....attribute import AttributeInputType
from ....attribute.models import AttributeValue
from ....page.error_codes import PageErrorCode
from ....product.error_codes import ProductErrorCode
from ..enums import AttributeValueBulkActionEnum
from ..utils import (
    AttributeAssignmentMixin,
    AttrValuesForSelectableFieldInput,
    AttrValuesInput,
    prepare_attribute_values,
    validate_attributes_input,
)


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_product(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_product_no_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_product_too_many_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["abc", "efg"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["a", "b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert error.params["attributes"] == [
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    ]


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_product_empty_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a", None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["  "],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_product_lack_of_required_attribute(
    weight_attribute, color_attribute, product_type
):
    # given
    product_attributes = product_type.product_attributes.all()
    attr = product_attributes.first()
    attr.value_required = True
    attr.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_attributes,
        is_page_attributes=False,
        creation=True,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_product_creation_multiple_errors(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["a", "b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

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


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_page(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        page_type.page_attributes.all(),
        is_page_attributes=True,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_page_no_values_given(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        page_type.page_attributes.all(),
        is_page_attributes=True,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_page_too_many_values_given(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["abc", "efg"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["a", "b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        page_type.page_attributes.all(),
        is_page_attributes=True,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.INVALID.value
    assert error.params["attributes"] == [
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    ]


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_for_page_empty_values_given(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a", None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["  "],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        page_type.page_attributes.all(),
        is_page_attributes=True,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_page_lack_of_required_attribute(
    weight_attribute, color_attribute, page_type
):
    # given
    page_attributes = page_type.page_attributes.all()
    attr = page_attributes.first()
    attr.value_required = True
    attr.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data, page_attributes, is_page_attributes=True, creation=True
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
    }


def test_validate_attributes_input_for_page_multiple_errors(
    weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["a", "b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        page_type.page_attributes.all(),
        is_page_attributes=True,
        creation=True,
    )

    # then
    assert len(errors) == 2
    assert {error.code for error in errors} == {
        PageErrorCode.INVALID.value,
        PageErrorCode.REQUIRED.value,
    }
    assert {attr for error in errors for attr in error.params["attributes"]} == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()

    # when
    errors = validate_attributes_input(
        input_data, attributes, is_page_attributes=False, creation=creation
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_no_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()

    # when
    errors = validate_attributes_input(
        input_data, attributes, is_page_attributes=False, creation=creation
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_duplicated_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["test", "new", "test"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["test", "test"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()

    # when
    errors = validate_attributes_input(
        input_data, attributes, is_page_attributes=False, creation=creation
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_not_required_variant_selection_attributes_input_no_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = False
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = False
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    # To be verified.
    product_type.variant_attributes.add(weight_attribute)
    product_type.variant_attributes.add(color_attribute)

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=[],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()
    # when
    errors = validate_attributes_input(
        input_data,
        attributes,
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_too_many_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["abc", "efg"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["a", "b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()

    # when
    errors = validate_attributes_input(
        input_data,
        attributes,
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_input_empty_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["  "],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()

    # when
    errors = validate_attributes_input(
        input_data, attributes, is_page_attributes=False, creation=creation
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_multiple_errors(
    weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=[None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                values=["a", "b"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    attributes = product_type.variant_attributes.all()

    # when
    errors = validate_attributes_input(
        input_data, attributes, is_page_attributes=False, creation=True
    )

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


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_with_file_input_type_for_product(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            file_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", file_attribute.pk),
                values=[],
                file_url="test_file.jpeg",
                content_type="image/jpeg",
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_with_file_input_type_for_product_no_file_given(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            file_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", file_attribute.pk),
                values=[],
                file_url="",
                content_type="image/jpeg",
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_not_required_attrs_with_file_input_type_for_product_no_file_given(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = False
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = False
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            file_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", file_attribute.pk),
                values=[],
                file_url="",
                content_type="image/jpeg",
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_attributes_with_file_input_type_for_product_empty_file_value(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                values=["a"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
        (
            file_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", file_attribute.pk),
                values=[],
                file_url="  ",
                content_type="image/jpeg",
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_input_for_product(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                values=["12.34"],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("value", ["qvd", "12.se", "  "])
@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_input_for_product_not_numeric_value_given(
    creation, value, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                values=[value],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_input_for_product_blank_value(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                values=[None],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_input_none_as_values(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                values=None,
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_input_for_product_more_than_one_value_given(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                values=["12", 1, 123],
                file_url=None,
                content_type=None,
                references=[],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attributes_by_value(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(value="new color"),
            ),
        ),
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(value="new weight 1"),
                    AttrValuesForSelectableFieldInput(value="new weight 2"),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attributes_by_id(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(id="id"),
            ),
        ),
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(id="id1"),
                    AttrValuesForSelectableFieldInput(id="id2"),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attributes_pass_null_value(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.save(update_fields=["input_type"])

    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(value=None),
            ),
        ),
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(value=None),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attribute_by_id_and_value(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(id="id", value="new color"),
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.INVALID.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attribute_by_external_reference(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(
                    external_reference=color_attribute.external_reference,
                    value="new color",
                ),
            ),
        )
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attribute_by_id_and_external_reference(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(
                    id="id", external_reference="external_reference"
                ),
            ),
        )
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.INVALID.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attribute_by_value_and_external_reference(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(
                    value="new color", external_reference="external_reference"
                ),
            ),
        )
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_multiselect_attribute_by_id_and_value(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(id="id"),
                    AttrValuesForSelectableFieldInput(value="new weight"),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.INVALID.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_multiselect_attribute_duplicated_values(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(value="new weight"),
                    AttrValuesForSelectableFieldInput(value="new weight"),
                    AttrValuesForSelectableFieldInput(value="new weight 2"),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_multiselect_attribute_duplicated_ids(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(id="new weight"),
                    AttrValuesForSelectableFieldInput(id="new weight"),
                    AttrValuesForSelectableFieldInput(id="new weight 2"),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_multiselect_attribute_duplicated_external_refs(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            weight_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", weight_attribute.pk),
                multiselect=[
                    AttrValuesForSelectableFieldInput(external_reference="newWeight"),
                    AttrValuesForSelectableFieldInput(external_reference="newWeight"),
                    AttrValuesForSelectableFieldInput(external_reference="newWeight2"),
                ],
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attribute_max_length_exceeded(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])
    col_max = color_attribute.values.model.name.field.max_length

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(value="n" * col_max + "n"),
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.INVALID.value


@pytest.mark.parametrize("value", [None, "", " "])
@pytest.mark.parametrize("creation", [True, False])
def test_validate_selectable_attribute_value_required(
    creation, value, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    input_data = [
        (
            color_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
                dropdown=AttrValuesForSelectableFieldInput(value=value),
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.REQUIRED.value


@pytest.mark.parametrize("value", [2.56, "2.56", "0", 0, -3.5, "-3.6"])
@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes(creation, value, numeric_attribute, product_type):
    # given
    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                numeric=value,
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("value", [True, "number", "0,56", "e-10", "20k"])
@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_invalid_number(
    creation, value, numeric_attribute, product_type
):
    # given
    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                numeric=value,
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.INVALID.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_pass_null_value(
    creation, numeric_attribute, product_type
):
    # given
    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                numeric=None,
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_value_required(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            numeric_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
                numeric=None,
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert len(errors) == 1
    assert errors[0].code == ProductErrorCode.REQUIRED.value


@pytest.mark.parametrize("creation", [True, False])
def test_validate_rich_text_attributes_input_for_product_only_embed_block(
    creation, rich_text_attribute, product_type
):
    # given
    rich_text_attribute.value_required = True
    rich_text_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            rich_text_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id(
                    "Attribute", rich_text_attribute.pk
                ),
                values=["12.34"],
                file_url=None,
                content_type=None,
                references=[],
                rich_text={
                    "time": 1670422589533,
                    "blocks": [
                        {
                            "id": "6sWdDeIffS",
                            "type": "embed",
                            "data": {
                                "service": "youtube",
                                "source": "https://www.youtube.com/watch?v=xyz",
                                "embed": "https://www.youtube.com/embed/xyz",
                                "width": 580,
                                "height": 320,
                                "caption": "How To Use",
                            },
                        }
                    ],
                    "version": "2.22.2",
                },
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


@pytest.mark.parametrize("creation", [True, False])
def test_validate_rich_text_attributes_input_for_product_only_image_block(
    creation, rich_text_attribute, product_type
):
    # given
    rich_text_attribute.value_required = True
    rich_text_attribute.save(update_fields=["value_required"])

    input_data = [
        (
            rich_text_attribute,
            AttrValuesInput(
                global_id=graphene.Node.to_global_id(
                    "Attribute", rich_text_attribute.pk
                ),
                values=["12.34"],
                file_url=None,
                content_type=None,
                references=[],
                rich_text={
                    "time": 1670422589533,
                    "blocks": [
                        {
                            "id": "6n7TFTMU8y",
                            "type": "image",
                            "data": {
                                "file": {"url": "https://codex.so/public/codex2x.png"},
                                "caption": "",
                                "withBorder": False,
                                "stretched": False,
                                "withBackground": False,
                            },
                        }
                    ],
                },
            ),
        ),
    ]

    # when
    errors = validate_attributes_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )

    # then
    assert not errors


def test_clean_file_url_in_attribute_assignment_mixin(site_settings):
    # given
    name = "Test.jpg"
    domain = site_settings.site.domain
    url = f"http://{domain}{settings.MEDIA_URL}{name}"

    # when
    result = AttributeAssignmentMixin._clean_file_url(url, ProductErrorCode)

    # then
    assert result == name


@pytest.mark.parametrize(
    "file_url",
    [
        "http://localhost:8000/media/Test.jpg",
        "/media/Test.jpg",
        "Test.jpg",
        "/ab/cd.jpg",
    ],
)
def test_clean_file_url_in_attribute_assignment_mixin_invalid_url(file_url):
    # when & then
    with pytest.raises(ValidationError):
        AttributeAssignmentMixin._clean_file_url(file_url, ProductErrorCode)


def test_prepare_attribute_values(color_attribute):
    # given
    existing_value = color_attribute.values.first()
    attr_values_count = color_attribute.values.count()
    new_value = existing_value.name.upper()
    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        # we should get the new value only for the last element
        values=[existing_value.name, existing_value.slug, new_value],
        file_url=None,
        content_type=None,
        references=[],
    )

    # when
    values_to_create = prepare_attribute_values(color_attribute, values.values)[1]
    AttributeValue.objects.bulk_create(values_to_create)

    # then
    color_attribute.refresh_from_db()
    assert color_attribute.values.count() == attr_values_count + 1
    assert color_attribute.values.last().name == new_value


def test_prepare_attribute_values_prefer_the_slug_match(color_attribute):
    """Ensure that the value with slug match is returned as the first choice.

    When the value with the matching slug is not found, the value with the matching
    name is returned.
    """
    # given
    existing_value = color_attribute.values.first()
    second_val = color_attribute.values.create(
        name=existing_value.slug, slug=f"{existing_value.slug}-2"
    )

    attr_values_count = color_attribute.values.count()

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        # we should get the new value only for the last element
        values=[existing_value.name, second_val.name, second_val.slug],
        file_url=None,
        content_type=None,
        references=[],
    )

    # when
    result, values_to_create = prepare_attribute_values(color_attribute, values.values)
    AttributeValue.objects.bulk_create(values_to_create)

    # then
    color_attribute.refresh_from_db()
    assert color_attribute.values.count() == attr_values_count
    assert result == [existing_value, existing_value, second_val]


def test_prepare_attribute_values_that_gives_the_same_slug(color_attribute):
    """Ensure that the unique slug for all values is created.

    Ensure that when providing the two or more values that are giving the same slug
    the integrity error is not raised.
    """
    # given
    existing_value = color_attribute.values.first()
    attr_values_count = color_attribute.values.count()
    new_value = "RED"
    new_value_2 = "ReD"

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        # we should get the new value only for the last element
        values=[existing_value.name, new_value, new_value_2],
        file_url=None,
        content_type=None,
        references=[],
    )

    # when
    result, values_to_create = prepare_attribute_values(color_attribute, values.values)
    AttributeValue.objects.bulk_create(values_to_create)

    # then
    color_attribute.refresh_from_db()
    assert color_attribute.values.count() == attr_values_count + 2
    assert len(result) == 3
    assert result[0] == existing_value
    assert result[1].name == new_value
    assert result[2].name == new_value_2


def test_attribute_assignment_mixin_pre_save_multiselect_external_reference_action(
    color_attribute,
):
    # given
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["input_type"])

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        content_type=None,
        references=[],
        multiselect=[
            AttrValuesForSelectableFieldInput(
                external_reference=value.external_reference
            )
            for value in color_attribute.values.all()
        ],
    )

    # when
    result = AttributeAssignmentMixin._pre_save_multiselect_values(
        None, color_attribute, values
    )

    # then
    assert result == [
        (AttributeValueBulkActionEnum.NONE, value)
        for value in color_attribute.values.all()
    ]
