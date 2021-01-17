import graphene

from ....attribute import AttributeInputType
from ....page.error_codes import PageErrorCode
from ....product.error_codes import ProductErrorCode
from ...product.mutations.products import AttrValuesInput
from ..utils import validate_attributes_input


def test_validate_attributes_input_for_product(
    weight_attribute, color_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert not errors


def test_validate_attributes_input_for_product_no_values_given(
    weight_attribute, color_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_product_too_many_values_given(
    weight_attribute, color_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert error.params["attributes"] == [
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    ]


def test_validate_attributes_input_for_product_empty_values_given(
    weight_attribute, color_attribute, product_type
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
        variant_validation=False,
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
    }


def test_validate_attributes_input_for_product_multiply_errors(
    weight_attribute, color_attribute, product_type
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
        variant_validation=False,
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


def test_validate_attributes_input_for_page(
    weight_attribute, color_attribute, page_type
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
        variant_validation=False,
    )

    # then
    assert not errors


def test_validate_attributes_input_for_page_no_values_given(
    weight_attribute, color_attribute, page_type
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_for_page_too_many_values_given(
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.INVALID.value
    assert error.params["attributes"] == [
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    ]


def test_validate_attributes_input_for_page_empty_values_given(
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
        variant_validation=False,
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
        input_data, page_attributes, is_page_attributes=True, variant_validation=False
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == PageErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
    }


def test_validate_attributes_input_for_page_multiply_errors(
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
        variant_validation=False,
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


def test_validate_attributes_input(weight_attribute, color_attribute, product_type):
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
        input_data, attributes, is_page_attributes=False, variant_validation=True
    )

    # then
    assert not errors


def test_validate_attributes_input_no_values_given(
    weight_attribute, color_attribute, product_type
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
        input_data, attributes, is_page_attributes=False, variant_validation=True
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_not_required_variant_selection_attributes_input_no_values_given(
    weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = False
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = False
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

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
        input_data, attributes, is_page_attributes=False, variant_validation=True
    )

    # then
    assert not errors


def test_validate_attributes_input_too_many_values_given(
    weight_attribute, color_attribute, product_type
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
        input_data, attributes, is_page_attributes=False, variant_validation=True
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_empty_values_given(
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
        input_data, attributes, is_page_attributes=False, variant_validation=True
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_validate_attributes_input_multiply_errors(
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
        input_data, attributes, is_page_attributes=False, variant_validation=True
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


def test_validate_attributes_with_file_input_type_for_product(
    weight_attribute, file_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert not errors


def test_validate_attributes_with_file_input_type_for_product_no_file_given(
    weight_attribute, file_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    }


def test_validate_not_required_attrs_with_file_input_type_for_product_no_file_given(
    weight_attribute, file_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert not errors


def test_validate_attributes_with_file_input_type_for_product_empty_file_value(
    weight_attribute, file_attribute, product_type
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
        variant_validation=False,
    )

    # then
    assert len(errors) == 1
    error = errors[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    }
