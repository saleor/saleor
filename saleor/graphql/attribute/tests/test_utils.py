from collections import defaultdict

import graphene
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from ....attribute import AttributeInputType
from ....product.error_codes import ProductErrorCode
from ..enums import AttributeValueBulkActionEnum
from ..utils.attribute_assignment import AttributeAssignmentMixin
from ..utils.shared import AttrValuesForSelectableFieldInput, AttrValuesInput
from ..utils.type_handlers import (
    FileAttributeHandler,
    MultiSelectableAttributeHandler,
    SelectableAttributeHandler,
)


@pytest.mark.parametrize("creation", [True, False])
def test_clean_input_for_product(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["b"],
        },
    ]

    # when & then
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_product_no_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_product_too_many_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["abc", "efg"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["a", "b", "c"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_product_empty_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a", None],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["  "],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_clean_attribute_input_for_product_lack_of_required_attribute(
    weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=True,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_product_creation_multiple_errors(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": [None],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["a", "b"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 2
    assert {error.code for error in exc_info.value.error_list} == {
        ProductErrorCode.INVALID.value,
        ProductErrorCode.REQUIRED.value,
    }
    assert {
        attr
        for error in exc_info.value.error_list
        for attr in error.params["attributes"]
    } == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_page(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    page_type.page_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["b"],
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        page_type.page_attributes.all(),
        is_page_attributes=True,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_page_no_values_given(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    page_type.page_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            page_type.page_attributes.all(),
            is_page_attributes=True,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_page_too_many_values_given(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    page_type.page_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["abc", "efg"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["a", "b"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            page_type.page_attributes.all(),
            is_page_attributes=True,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attribute_input_for_page_empty_values_given(
    creation, weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    page_type.page_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a", None],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["  "],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            page_type.page_attributes.all(),
            is_page_attributes=True,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


def test_clean_attribute_input_for_page_lack_of_required_attribute(
    weight_attribute, color_attribute, page_type
):
    # given
    page_attributes = page_type.page_attributes.all()
    attr = page_attributes.first()
    attr.value_required = True
    attr.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    page_type.page_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data, page_attributes, is_page_attributes=True, creation=True
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
    }


def test_clean_attribute_input_for_page_multiple_errors(
    weight_attribute, color_attribute, page_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    page_type.page_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["a", "b"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            page_type.page_attributes.all(),
            is_page_attributes=True,
            creation=True,
        )

    # then
    assert len(exc_info.value.error_list) == 2
    assert {error.code for error in exc_info.value.error_list} == {
        ProductErrorCode.INVALID.value,
        ProductErrorCode.REQUIRED.value,
    }
    assert {
        attr
        for error in exc_info.value.error_list
        for attr in error.params["attributes"]
    } == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_input(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["b"],
        },
    ]

    # when & then
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.variant_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_input_no_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.variant_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_duplicated_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["test", "new", "test"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["test", "test"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.variant_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_input_empty_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.value_required = False
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = False
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
        },
    ]

    # when & then
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.variant_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_too_many_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["abc", "efg"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["a", "b"],
        },
    ]

    # when & then
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.variant_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [color_attribute, weight_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_empty_values_given(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": [None],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": [" "],
        },
    ]

    # when & then
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.variant_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [color_attribute, weight_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_variant_attribute_input_multiple_errors(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    weight_attribute.value_required = True
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.variant_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": [None],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "values": ["a", "b"],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.variant_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 2
    assert {error.code for error in exc_info.value.error_list} == {
        ProductErrorCode.INVALID.value,
        ProductErrorCode.REQUIRED.value,
    }
    assert {
        attr
        for error in exc_info.value.error_list
        for attr in error.params["attributes"]
    } == {
        graphene.Node.to_global_id("Attribute", attr.pk)
        for attr in [weight_attribute, color_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attributes_with_file_input_type_for_product(
    creation, weight_attribute, file_attribute, product_type, site_settings
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])
    product_type.product_attributes.add(weight_attribute, file_attribute)

    domain = site_settings.site.domain
    file_url = f"http://{domain}{settings.MEDIA_URL}test_file.jpeg"

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
            "file": file_url,
            "content_type": "image/jpeg",
        },
    ]

    # when & then
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attributes_with_file_input_type_for_product_no_file_given(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(weight_attribute, file_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", attr.pk) for attr in [file_attribute]
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_not_required_attrs_with_file_input_type_for_product_no_file_given(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = False
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = False
    weight_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(weight_attribute, file_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_attributes_with_file_input_type_for_product_empty_file_value(
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])

    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(weight_attribute, file_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "values": ["a"],
        },
        {
            "id": graphene.Node.to_global_id("Attribute", file_attribute.pk),
            "values": ["  "],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", file_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_numeric_attributes_input_for_product(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "values": ["12.34"],
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("value", ["qvd", "12.se", "  "])
@pytest.mark.parametrize("creation", [True, False])
def test_clean_numeric_attributes_input_for_product_not_numeric_value_given(
    creation, value, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "values": [value],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
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

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "values": [None],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
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

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
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

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "values": ["12", 1, 123],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
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

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(value="new color"),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [
                AttrValuesForSelectableFieldInput(value="new weight 1"),
                AttrValuesForSelectableFieldInput(value="new weight 2"),
            ],
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


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

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(id="id"),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [
                AttrValuesForSelectableFieldInput(id="id1"),
                AttrValuesForSelectableFieldInput(id="id2"),
            ],
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attributes_pass_null_value(
    creation, weight_attribute, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.save(update_fields=["input_type"])

    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.save(update_fields=["input_type"])

    product_type.product_attributes.add(color_attribute, weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(value=None),
        },
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [AttrValuesForSelectableFieldInput(value=None)],
        },
    ]

    # when & then
    # no errors should be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attribute_by_id_and_value(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(
                value="new color",
                id="id",
            ),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attribute_by_external_reference(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(
                value="new color",
                external_reference=color_attribute.external_reference,
            ),
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attribute_by_id_and_external_reference(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(
                id="id",
                external_reference="external_reference",
            ),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attribute_by_value_and_external_reference(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(
                value="new color",
                external_reference="external_reference",
            ),
        },
    ]

    # when & then
    # no errors should be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_multiselect_attribute_by_id_and_value(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [
                AttrValuesForSelectableFieldInput(id="id"),
                AttrValuesForSelectableFieldInput(value="new weight"),
            ],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", weight_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_multiselect_attribute_duplicated_values(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [
                AttrValuesForSelectableFieldInput(value="new weight"),
                AttrValuesForSelectableFieldInput(value="new weight"),
                AttrValuesForSelectableFieldInput(value="new weight 2"),
            ],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", weight_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_multiselect_attribute_duplicated_ids(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [
                AttrValuesForSelectableFieldInput(id="newWeight"),
                AttrValuesForSelectableFieldInput(id="newWeight"),
                AttrValuesForSelectableFieldInput(id="newWeight2"),
            ],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", weight_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_multiselect_attribute_duplicated_external_refs(
    creation, weight_attribute, product_type
):
    # given
    weight_attribute.input_type = AttributeInputType.MULTISELECT
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(weight_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", weight_attribute.pk),
            "multiselect": [
                AttrValuesForSelectableFieldInput(external_reference="newWeight"),
                AttrValuesForSelectableFieldInput(external_reference="newWeight"),
                AttrValuesForSelectableFieldInput(external_reference="newWeight2"),
            ],
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.DUPLICATED_INPUT_ITEM.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", weight_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attribute_max_length_exceeded(
    creation, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])
    col_max = color_attribute.values.model.name.field.max_length

    product_type.product_attributes.add(color_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(value="n" * col_max + "n"),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("value", [None, ""])
@pytest.mark.parametrize("creation", [True, False])
def test_clean_selectable_attribute_value_required(
    creation, value, color_attribute, product_type
):
    # given
    color_attribute.input_type = AttributeInputType.DROPDOWN
    color_attribute.value_required = True
    color_attribute.save(update_fields=["value_required", "input_type"])

    product_type.product_attributes.add(color_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", color_attribute.pk),
            "dropdown": AttrValuesForSelectableFieldInput(value=value),
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", color_attribute.pk)
    }


@pytest.mark.parametrize("value", [2.56, "2.56", "0", 0, -3.5, "-3.6"])
@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes(creation, value, numeric_attribute, product_type):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "numeric": value,
        },
    ]

    # when
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("value", [True, "number", "0,56", "e-10", "20k"])
@pytest.mark.parametrize("creation", [True, False])
def test_validate_numeric_attributes_invalid_number(
    creation, value, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])

    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "numeric": value,
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.INVALID.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_clean_numeric_attributes_pass_null_value(
    creation, numeric_attribute, product_type
):
    # given
    product_type.product_attributes.add(numeric_attribute)
    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "numeric": None,
        },
    ]

    # when & then
    # no errors should be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_numeric_attributes_value_required(
    creation, numeric_attribute, product_type
):
    # given
    numeric_attribute.value_required = True
    numeric_attribute.save(update_fields=["value_required"])
    product_type.product_attributes.add(numeric_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", numeric_attribute.pk),
            "numeric": None,
        },
    ]

    # when
    with pytest.raises(ValidationError) as exc_info:
        AttributeAssignmentMixin.clean_input(
            input_data,
            product_type.product_attributes.all(),
            is_page_attributes=False,
            creation=creation,
        )

    # then
    assert len(exc_info.value.error_list) == 1
    error = exc_info.value.error_list[0]
    assert error.code == ProductErrorCode.REQUIRED.value
    assert set(error.params["attributes"]) == {
        graphene.Node.to_global_id("Attribute", numeric_attribute.pk)
    }


@pytest.mark.parametrize("creation", [True, False])
def test_validate_rich_text_attributes_input_for_product_only_embed_block(
    creation, rich_text_attribute, product_type
):
    # given
    rich_text_attribute.value_required = True
    rich_text_attribute.save(update_fields=["value_required"])
    product_type.product_attributes.add(rich_text_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", rich_text_attribute.pk),
            "rich_text": {
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
        }
    ]

    # when & then
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


@pytest.mark.parametrize("creation", [True, False])
def test_clean_rich_text_attributes_input_for_product_only_image_block(
    creation, rich_text_attribute, product_type
):
    # given
    rich_text_attribute.value_required = True
    rich_text_attribute.save(update_fields=["value_required"])
    product_type.product_attributes.add(rich_text_attribute)

    input_data = [
        {
            "id": graphene.Node.to_global_id("Attribute", rich_text_attribute.pk),
            "rich_text": {
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
                "version": "2.22.2",
            },
        }
    ]

    # when & then
    # error shouldn't be raised
    AttributeAssignmentMixin.clean_input(
        input_data,
        product_type.product_attributes.all(),
        is_page_attributes=False,
        creation=creation,
    )


def test_clean_file_url(site_settings, file_attribute):
    # given
    name = "Test.jpg"
    domain = site_settings.site.domain
    url = f"http://{domain}{settings.MEDIA_URL}{name}"

    file_handler = FileAttributeHandler(
        file_attribute,
        AttrValuesInput(
            global_id=graphene.Node.to_global_id("Attribute", file_attribute.pk),
            values=[],
            file_url=url,
            content_type=None,
            references=[],
        ),
    )
    errors = defaultdict(list)

    # when
    file_handler.clean_and_validate(errors)

    # then
    assert not errors
    assert file_handler.values_input.file_url == name


@pytest.mark.parametrize(
    "file_url",
    [
        "http://localhost:8000/media/Test.jpg",
        "/media/Test.jpg",
        "Test.jpg",
        "/ab/cd.jpg",
    ],
)
def test_clean_file_url_in_attribute_assignment_mixin_invalid_url(
    file_url, file_attribute
):
    # given
    file_handler = FileAttributeHandler(
        file_attribute,
        AttrValuesInput(
            global_id=graphene.Node.to_global_id("Attribute", file_attribute.pk),
            values=[],
            file_url=file_url,
            content_type=None,
            references=[],
        ),
    )
    errors = defaultdict(list)

    # when & then
    file_handler.clean_and_validate(errors)

    assert errors


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
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    results = handler.prepare_attribute_values(color_attribute, values.values)

    # then
    pre_save_bulk = defaultdict(lambda: defaultdict(list))
    for action, value_data in results:
        pre_save_bulk[action][color_attribute].append(value_data)
    AttributeAssignmentMixin._bulk_create_pre_save_values(pre_save_bulk)

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
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    results = handler.prepare_attribute_values(color_attribute, values.values)

    # then
    pre_save_bulk = defaultdict(lambda: defaultdict(list))
    for action, value_data in results:
        pre_save_bulk[action][color_attribute].append(value_data)
    AttributeAssignmentMixin._bulk_create_pre_save_values(pre_save_bulk)

    color_attribute.refresh_from_db()
    assert color_attribute.values.count() == attr_values_count
    assert [result[1] for result in results] == [
        existing_value,
        existing_value,
        second_val,
    ]


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
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    results = handler.prepare_attribute_values(color_attribute, values.values)

    # then
    pre_save_bulk = defaultdict(lambda: defaultdict(list))
    for action, value_data in results:
        pre_save_bulk[action][color_attribute].append(value_data)
    AttributeAssignmentMixin._bulk_create_pre_save_values(pre_save_bulk)

    color_attribute.refresh_from_db()
    assert color_attribute.values.count() == attr_values_count + 2
    assert len(results) == 3
    assert results[0][1] == existing_value
    assert results[1][1].name == new_value
    assert results[2][1].name == new_value_2


def test_pre_save_multiselect_external_reference_action(color_attribute, product):
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
    handler = MultiSelectableAttributeHandler(color_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [
        (AttributeValueBulkActionEnum.NONE, value)
        for value in color_attribute.values.all()
    ]
