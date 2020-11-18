from ...attribute import AttributeInputType
from ..utils.variants import get_variant_selection_attributes


def test_get_variant_selection_attributes(
    product_type_attribute_list, image_attribute_without_values_and_file_input_type
):
    # given
    multiselect_attr = product_type_attribute_list[0]
    multiselect_attr.input_type = AttributeInputType.MULTISELECT
    multiselect_attr.save(update_fields=["input_type"])

    attrs = product_type_attribute_list + [
        image_attribute_without_values_and_file_input_type
    ]

    # when
    result = get_variant_selection_attributes(attrs)

    # then
    assert result == product_type_attribute_list[1:]
