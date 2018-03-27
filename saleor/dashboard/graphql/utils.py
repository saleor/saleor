from saleor.product import models


def get_attributes_dict_from_list(attributes):
    """
    :param attributes: list
    :return: dict
    Takes list on form [{"slug": "attr_slug", "value": "attr_value"}, {...}]
    and converts into dictionary {attr_pk: value_pk}
    """

    attr_ids = {}
    attr_slug_id = dict(
        models.ProductAttribute.objects.values_list('slug', 'id'))
    value_slug_id = dict(
        models.AttributeChoiceValue.objects.values_list('name', 'id'))
    for attribute in attributes:
        attr_slug = attribute.get('slug')
        if attr_slug not in attr_slug_id:
            raise ValueError(
                'Unknown attribute slug: %r' % (attr_slug,))
        attr_value = attribute.get('value')
        attr_ids[attr_slug_id.get(
            attr_slug)] = value_slug_id.get(attr_value)
    return attr_ids
