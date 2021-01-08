from ...attribute import AttributeInputType
from ..utils.variants import get_variant_selection_attributes


def test_get_variant_selection_attributes(
    product_type_attribute_list,
    file_attribute_with_file_input_type_without_values,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
):
    # given
    multiselect_attr = product_type_attribute_list[0]
    multiselect_attr.input_type = AttributeInputType.MULTISELECT
    multiselect_attr.save(update_fields=["input_type"])

    attrs = product_type_attribute_list + [
        file_attribute_with_file_input_type_without_values,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
    ]

    # when
    result = get_variant_selection_attributes(attrs)

    # then
    assert result == product_type_attribute_list[1:]
