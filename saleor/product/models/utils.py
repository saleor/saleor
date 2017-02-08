from django.utils.encoding import smart_text
from typing import Dict, Iterable, Union


def get_attributes_display_map(obj, attributes):
    from .base import AttributeChoiceValue, Product, ProductAttribute, ProductVariant
    # type: (Union[Product, ProductVariant], Iterable[ProductAttribute]) -> Dict[str, Union[AttributeChoiceValue, str]]
    display_map = {}
    for attribute in attributes:
        value = obj.attributes.get(smart_text(attribute.pk))
        if value:
            choices = {smart_text(a.pk): a for a in attribute.values.all()}
            choice_obj = choices.get(value)
            if choice_obj:
                display_map[attribute.pk] = choice_obj
            else:
                display_map[attribute.pk] = value
    return display_map
