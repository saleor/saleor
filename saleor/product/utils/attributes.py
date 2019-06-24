from collections import defaultdict
from typing import List


def get_product_attributes_data(product):
    """Return the attributes associated with the product.

    It is returned as a dict of Attribute: AttributeValue values.
    """
    attributes = product.product_type.product_attributes.all()
    attributes_map = {attribute.pk: attribute.translated for attribute in attributes}
    values_map = get_attributes_display_map(product, attributes)
    return {
        attributes_map[attr_pk]: value_obj.translated
        for (attr_pk, value_obj) in values_map.items()
    }


def get_name_from_attributes(variant, attributes):
    """Generate ProductVariant's name based on its attributes."""
    values = get_attributes_display_map(variant, attributes)
    return generate_name_from_values(values)


def get_attributes_display_map(obj, attributes):
    """Return attributes associated with an object, as dict of AttrPK: AttributeValue.

    Args:
        obj: The variant or product.
        attributes: Attribute Iterable

    """
    display_map = defaultdict(str)
    for attribute in attributes:
        values = obj.attributes.get(str(attribute.pk))  # type: List
        if values:
            choices = {str(a.pk): a.translated for a in attribute.values.all()}
            for value in values:
                current_display_value = display_map[attribute.pk]
                if not current_display_value:
                    current_display_value = choices[value]
                else:
                    current_display_value = f"{current_display_value}, {choices[value]}"
                display_map[attribute.pk] = current_display_value
    return display_map


def generate_name_from_values(attributes_dict):
    """Generate name from AttributeValues.

    Attributes dict is sorted, as attributes order should be kept within each save.

    Args:
        attributes_dict: dict of attribute_pk: AttributeValue values

    """
    return " / ".join(
        str(attribute_value)
        for attribute_pk, attribute_value in sorted(
            attributes_dict.items(), key=lambda x: x[0]
        )
    )
