import datetime
from collections import defaultdict

import graphene
import pytest
from django.conf import settings
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....attribute import AttributeInputType
from ....attribute.models import AttributeValue
from ....attribute.utils import associate_attribute_values_to_instance
from ....product.error_codes import ProductErrorCode
from ..enums import AttributeValueBulkActionEnum
from ..shared_filters import validate_attribute_value_input
from ..utils.attribute_assignment import AttributeAssignmentMixin
from ..utils.shared import (
    AttrValuesForSelectableFieldInput,
    AttrValuesInput,
    has_input_modified_attribute_values,
)
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
    creation, weight_attribute, file_attribute, product_type
):
    # given
    file_attribute.value_required = True
    file_attribute.save(update_fields=["value_required"])
    weight_attribute.value_required = True
    weight_attribute.save(update_fields=["value_required"])
    product_type.product_attributes.add(weight_attribute, file_attribute)

    file_url = f"https://example.com{settings.MEDIA_URL}test_file.jpeg"

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


def test_clean_file_url(file_attribute):
    # given
    name = "Test.jpg"
    url = f"https://example.com{settings.MEDIA_URL}{name}"

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


def test_pre_save_multiselect_with_id(
    color_attribute,
    product,
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
                id=graphene.Node.to_global_id("AttributeValue", value.pk)
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


def test_pre_save_multiselect_external_reference_and_value(
    color_attribute,
    product,
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
                external_reference=value.external_reference, value=value.name
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


def test_pre_save_multiselect_external_reference_and_invalid_value(
    multiselect_attribute,
    product,
):
    # given
    values = list(multiselect_attribute.values.all())
    external_refs = []
    for value in values:
        value.external_reference = f"ext-ref-{value.pk}"
        external_refs.append(value.external_reference)

    AttributeValue.objects.bulk_update(values, ["external_reference"])

    values_input = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", multiselect_attribute.pk),
        content_type=None,
        references=[],
        multiselect=[
            AttrValuesForSelectableFieldInput(
                external_reference=external_ref, value="not-matching-value"
            )
            for external_ref in external_refs
        ],
    )
    handler = MultiSelectableAttributeHandler(multiselect_attribute, values_input)

    # when & then
    with pytest.raises(ValidationError) as exc_info:
        handler.pre_save_value(product)

    message = str(exc_info.value)
    assert "Attribute value with external reference" in message


def test_pre_save_multiselect_external_reference_and_new_value(
    color_attribute,
    product,
):
    # given
    color_attribute.input_type = AttributeInputType.MULTISELECT
    color_attribute.save(update_fields=["input_type"])
    new_value = "New Color"

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        content_type=None,
        references=[],
        multiselect=[
            AttrValuesForSelectableFieldInput(
                external_reference="new-external-reference", value=new_value
            )
        ],
    )
    handler = MultiSelectableAttributeHandler(color_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert len(result) == 1
    action, value = result[0]
    assert action == AttributeValueBulkActionEnum.CREATE
    assert value.name == new_value


@pytest.mark.parametrize(
    ("attribute_fixture", "value_payload"),
    [
        (
            "product_type_product_reference_attribute",
            {"reference": {"productIds": {"containsAny": ["ref-id"]}}},
        ),
        (
            "product_type_product_single_reference_attribute",
            {"reference": {"productVariantSkus": {"containsAny": ["SKU123"]}}},
        ),
    ],
)
def test_validate_attribute_value_input_accepts_reference_payloads(
    request, attribute_fixture, value_payload
):
    attribute = request.getfixturevalue(attribute_fixture)
    attributes = [{"slug": attribute.slug, "value": value_payload}]

    # when & then
    validate_attribute_value_input(attributes, "default")


@pytest.mark.parametrize(
    ("attribute_fixture", "value_payload"),
    [
        (
            "product_type_product_reference_attribute",
            {"numeric": {"gte": 10}},
        ),
        (
            "product_type_product_single_reference_attribute",
            {"numeric": {"gte": 10}},
        ),
    ],
)
def test_validate_attribute_value_input_rejects_invalid_reference_payloads(
    request, attribute_fixture, value_payload
):
    attribute = request.getfixturevalue(attribute_fixture)
    attributes = [{"slug": attribute.slug, "value": value_payload}]

    with pytest.raises(GraphQLError) as exc_info:
        validate_attribute_value_input(attributes, "default")

    message = str(exc_info.value)
    assert "Incorrect input for attributes on position: 0" in message
    assert "do not match the attribute input type" in message


def test_validate_attribute_value_input_rejects_numeric_reference(numeric_attribute):
    attributes = [
        {
            "slug": numeric_attribute.slug,
            "value": {
                "reference": {"productIds": {"containsAny": ["ref"]}},
            },
        }
    ]

    with pytest.raises(GraphQLError) as exc_info:
        validate_attribute_value_input(attributes, "default")

    message = str(exc_info.value)
    assert "Incorrect input for attributes on position: 0" in message
    assert "do not match the attribute input type" in message


@pytest.mark.parametrize(
    "attributes",
    [
        [{"slug": "attr", "value": {}}],
        [{"slug": "attr", "value": None}],
    ],
)
def test_validate_attribute_value_input_rejects_empty_values(attributes):
    with pytest.raises(GraphQLError) as exc_info:
        validate_attribute_value_input(attributes, "default")

    message = str(exc_info.value)
    assert "Incorrect input for attributes on position: 0" in message
    assert "cannot be empty or null" in message


def test_validate_attribute_value_input_rejects_multiple_value_keys():
    attributes = [
        {
            "slug": "attr",
            "value": {"slug": "value1", "name": "value2"},
        }
    ]

    with pytest.raises(GraphQLError) as exc_info:
        validate_attribute_value_input(attributes, "default")

    message = str(exc_info.value)
    assert "Incorrect input for attributes on position: 0" in message
    assert "must have only one input key" in message


def test_validate_attribute_value_input_combines_invalid_entries(
    product_type_product_reference_attribute,
    numeric_attribute,
    boolean_attribute,
):
    attributes = [
        {
            "slug": product_type_product_reference_attribute.slug,
            "value": {"numeric": {"gte": 1}},
        },
        {
            "slug": numeric_attribute.slug,
            "value": {"boolean": True},
        },
        {
            "slug": boolean_attribute.slug,
            "value": {"reference": {"productIds": {"containsAny": ["ref"]}}},
        },
    ]

    with pytest.raises(GraphQLError) as exc_info:
        validate_attribute_value_input(attributes, "default")

    message = str(exc_info.value)
    assert "Incorrect input for attributes on position: 0,1,2" in message
    assert "do not match the attribute input type" in message


def test_pre_save_dropdown_with_id(
    color_attribute,
    product,
):
    # given
    first_value = color_attribute.values.first()
    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        content_type=None,
        references=[],
        dropdown=AttrValuesForSelectableFieldInput(
            id=graphene.Node.to_global_id("AttributeValue", first_value.pk)
        ),
    )
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [(AttributeValueBulkActionEnum.NONE, first_value)]


def test_pre_save_dropdown_external_reference_action(
    color_attribute,
    product,
):
    # given
    first_value = color_attribute.values.first()
    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        content_type=None,
        references=[],
        dropdown=AttrValuesForSelectableFieldInput(
            external_reference=first_value.external_reference
        ),
    )
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [(AttributeValueBulkActionEnum.NONE, first_value)]


def test_pre_save_dropdown_external_reference_and_value(
    color_attribute,
    product,
):
    # given
    first_value = color_attribute.values.first()
    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        content_type=None,
        references=[],
        dropdown=AttrValuesForSelectableFieldInput(
            external_reference=first_value.external_reference, value=first_value.name
        ),
    )
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [(AttributeValueBulkActionEnum.NONE, first_value)]


def test_pre_save_dropdown_external_reference_and_new_value(
    color_attribute,
    product,
):
    # given
    new_value = "New Color"

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", color_attribute.pk),
        content_type=None,
        references=[],
        dropdown=AttrValuesForSelectableFieldInput(
            external_reference="new-external-reference", value=new_value
        ),
    )
    handler = SelectableAttributeHandler(color_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert len(result) == 1
    action, value = result[0]
    assert action == AttributeValueBulkActionEnum.CREATE
    assert value.name == new_value


def test_pre_save_swatch_with_id(
    swatch_attribute,
    product,
):
    # given
    first_value = swatch_attribute.values.first()
    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", swatch_attribute.pk),
        content_type=None,
        references=[],
        swatch=AttrValuesForSelectableFieldInput(
            id=graphene.Node.to_global_id("AttributeValue", first_value.pk)
        ),
    )
    handler = SelectableAttributeHandler(swatch_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [(AttributeValueBulkActionEnum.NONE, first_value)]


def test_pre_save_swatch_external_reference(
    swatch_attribute,
    product,
):
    # given
    first_value = swatch_attribute.values.first()
    external_reference = "swatch-external-reference"
    first_value.external_reference = external_reference
    first_value.save(update_fields=["external_reference"])

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", swatch_attribute.pk),
        content_type=None,
        references=[],
        swatch=AttrValuesForSelectableFieldInput(external_reference=external_reference),
    )
    handler = SelectableAttributeHandler(swatch_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [(AttributeValueBulkActionEnum.NONE, first_value)]


def test_pre_save_swatch_external_reference_and_value(
    swatch_attribute,
    product,
):
    # given
    first_value = swatch_attribute.values.first()
    external_reference = "swatch-external-reference"
    first_value.external_reference = external_reference
    first_value.save(update_fields=["external_reference"])
    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", swatch_attribute.pk),
        content_type=None,
        references=[],
        swatch=AttrValuesForSelectableFieldInput(
            external_reference=external_reference, value=first_value.name
        ),
    )
    handler = SelectableAttributeHandler(swatch_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert result == [(AttributeValueBulkActionEnum.NONE, first_value)]


def test_pre_save_swatch_external_reference_and_new_value(
    swatch_attribute,
    product,
):
    # given
    new_value = "New Color"

    values = AttrValuesInput(
        global_id=graphene.Node.to_global_id("Attribute", swatch_attribute.pk),
        content_type=None,
        references=[],
        swatch=AttrValuesForSelectableFieldInput(
            external_reference="new-external-reference", value=new_value
        ),
    )
    handler = SelectableAttributeHandler(swatch_attribute, values)

    # when
    result = handler.pre_save_value(product)

    # then
    assert len(result) == 1
    action, value = result[0]
    assert action == AttributeValueBulkActionEnum.CREATE
    assert value.name == new_value


def test_has_input_modified_attribute_values_no_changes_boolean(
    variant, boolean_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(boolean_attribute)
    value = boolean_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {boolean_attribute.id: [boolean_attribute.values.first()]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.GET_OR_CREATE: {
            boolean_attribute: [
                {
                    "attribute": boolean_attribute,
                    "slug": value.slug,
                    "defaults": {
                        "name": f"{boolean_attribute.name}: Yes",
                        "boolean": True,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_boolean(
    variant, boolean_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(boolean_attribute)
    associate_attribute_values_to_instance(
        variant,
        {boolean_attribute.id: [boolean_attribute.values.first()]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.GET_OR_CREATE: {
            boolean_attribute: [
                {
                    "attribute": boolean_attribute,
                    "slug": f"{boolean_attribute.id}_False",
                    "defaults": {
                        "name": f"{boolean_attribute.name}: No",
                        "boolean": False,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_dropdown(
    variant, color_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(color_attribute)
    first_value = color_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {color_attribute.id: [first_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.NONE: {color_attribute: [first_value]}
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_dropdown(
    variant, color_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(color_attribute)
    first_value = color_attribute.values.first()
    last_value = color_attribute.values.last()
    associate_attribute_values_to_instance(
        variant,
        {color_attribute.id: [first_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.NONE: {color_attribute: [last_value]}
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_multiselect(
    variant, multiselect_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(multiselect_attribute)
    all_values = list(multiselect_attribute.values.all())
    associate_attribute_values_to_instance(
        variant,
        {multiselect_attribute.id: all_values},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.NONE: {multiselect_attribute: all_values}
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_multiselect_order(
    variant, multiselect_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(multiselect_attribute)
    all_values = list(multiselect_attribute.values.all())
    associate_attribute_values_to_instance(
        variant,
        {multiselect_attribute.id: all_values},
    )
    # Change order of values
    reversed_values = list(reversed(all_values))
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.NONE: {multiselect_attribute: reversed_values}
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_plain_text(
    variant, plain_text_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(plain_text_attribute)
    text_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {plain_text_attribute.id: [text_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            plain_text_attribute: [
                {
                    "attribute": plain_text_attribute,
                    "slug": f"{variant.id}_{plain_text_attribute.id}",
                    "defaults": {
                        "plain_text": text_value.plain_text,
                        "name": text_value.name,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_plain_text(
    variant, plain_text_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(plain_text_attribute)
    text_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {plain_text_attribute.id: [text_value]},
    )
    different_text = "Different text"
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            plain_text_attribute: [
                {
                    "attribute": plain_text_attribute,
                    "slug": f"{variant.id}_{plain_text_attribute.id}",
                    "defaults": {
                        "plain_text": different_text,
                        "name": different_text[:200],
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_rich_text(
    variant, rich_text_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(rich_text_attribute)
    rich_text_value = rich_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {rich_text_attribute.id: [rich_text_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            rich_text_attribute: [
                {
                    "attribute": rich_text_attribute,
                    "slug": f"{variant.id}_{rich_text_attribute.id}",
                    "defaults": {
                        "rich_text": rich_text_value.rich_text,
                        "name": rich_text_value.name,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_rich_text(
    variant, rich_text_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(rich_text_attribute)
    rich_text_value = rich_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {rich_text_attribute.id: [rich_text_value]},
    )
    different_rich_text = {
        "blocks": [{"type": "paragraph", "data": {"text": "New content"}}]
    }
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            rich_text_attribute: [
                {
                    "attribute": rich_text_attribute,
                    "slug": f"{variant.id}_{rich_text_attribute.id}",
                    "defaults": {
                        "rich_text": different_rich_text,
                        "name": "New content"[:200],
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_numeric(
    variant, numeric_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(numeric_attribute)
    numeric_value = numeric_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {numeric_attribute.id: [numeric_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            numeric_attribute: [
                {
                    "attribute": numeric_attribute,
                    "slug": f"{variant.id}_{numeric_attribute.id}",
                    "defaults": {
                        "name": str(numeric_value.numeric),
                        "numeric": numeric_value.numeric,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_numeric(
    variant, numeric_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(numeric_attribute)
    numeric_value = numeric_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {numeric_attribute.id: [numeric_value]},
    )
    different_numeric = 100.5
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            numeric_attribute: [
                {
                    "attribute": numeric_attribute,
                    "slug": f"{variant.id}_{numeric_attribute.id}",
                    "defaults": {
                        "name": str(different_numeric),
                        "numeric": different_numeric,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_date(variant, date_attribute):
    # given
    variant.product.product_type.variant_attributes.add(date_attribute)
    date_value = date_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {date_attribute.id: [date_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            date_attribute: [
                {
                    "attribute": date_attribute,
                    "slug": f"{variant.id}_{date_attribute.id}",
                    "defaults": {
                        "name": str(date_value.date_time.date()),
                        "date_time": date_value.date_time,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_date(variant, date_attribute):
    # given
    variant.product.product_type.variant_attributes.add(date_attribute)
    date_value = date_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {date_attribute.id: [date_value]},
    )
    different_date = datetime.date(2021, 1, 1)
    different_date_time = datetime.datetime.combine(
        different_date, datetime.time.min, tzinfo=datetime.UTC
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            date_attribute: [
                {
                    "attribute": date_attribute,
                    "slug": f"{variant.id}_{date_attribute.id}",
                    "defaults": {
                        "name": str(different_date),
                        "date_time": different_date_time,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_no_changes_date_time(
    variant, date_time_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(date_time_attribute)
    date_time_value = date_time_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {date_time_attribute.id: [date_time_value]},
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            date_time_attribute: [
                {
                    "attribute": date_time_attribute,
                    "slug": f"{variant.id}_{date_time_attribute.id}",
                    "defaults": {
                        "name": str(date_time_value.date_time),
                        "date_time": date_time_value.date_time,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False


def test_has_input_modified_attribute_values_with_changes_date_time(
    variant, date_time_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(date_time_attribute)
    date_time_value = date_time_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {date_time_attribute.id: [date_time_value]},
    )
    different_date_time = datetime.datetime(2021, 5, 10, 14, 30, tzinfo=datetime.UTC)
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            date_time_attribute: [
                {
                    "attribute": date_time_attribute,
                    "slug": f"{variant.id}_{date_time_attribute.id}",
                    "defaults": {
                        "name": str(different_date_time),
                        "date_time": different_date_time,
                    },
                }
            ]
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_multiple_attributes(
    variant, color_attribute, size_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(color_attribute, size_attribute)
    color_first = color_attribute.values.first()
    size_first = size_attribute.values.first()
    size_last = size_attribute.values.last()
    associate_attribute_values_to_instance(
        variant,
        {
            color_attribute.id: [color_first],
            size_attribute.id: [size_first],
        },
    )
    # Change only one attribute
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.NONE: {
            color_attribute: [color_first],
            size_attribute: [size_last],
        }
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is True


def test_has_input_modified_attribute_values_mixed_bulk_actions(
    variant, color_attribute, plain_text_attribute
):
    # given
    variant.product.product_type.variant_attributes.add(
        color_attribute, plain_text_attribute
    )
    color_first = color_attribute.values.first()
    text_value = plain_text_attribute.values.first()
    associate_attribute_values_to_instance(
        variant,
        {
            color_attribute.id: [color_first],
            plain_text_attribute.id: [text_value],
        },
    )
    pre_save_bulk_data = {
        AttributeValueBulkActionEnum.NONE: {color_attribute: [color_first]},
        AttributeValueBulkActionEnum.UPDATE_OR_CREATE: {
            plain_text_attribute: [
                {
                    "attribute": plain_text_attribute,
                    "slug": f"{variant.id}_{plain_text_attribute.id}",
                    "defaults": {
                        "plain_text": text_value.plain_text,
                        "name": text_value.name,
                    },
                }
            ]
        },
    }

    # when
    result = has_input_modified_attribute_values(variant, pre_save_bulk_data)

    # then
    assert result is False
