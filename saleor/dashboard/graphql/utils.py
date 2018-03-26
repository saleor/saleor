from saleor.product import models

def get_attributes_dict_from_list(attributes):
    """
    :param attributes: list
    :return: dict
    Takes list on form [{"name": "attr_name", "value": "attr_value"}, {...}]
    and converts into dictionary {attr_pk: value_pk}
    """

    attr_ids = {}
    attr_name_id = dict(
        models.ProductAttribute.objects.values_list('name', 'id'))
    value_name_id = dict(
        models.AttributeChoiceValue.objects.values_list('name', 'id'))
    for attribute in attributes:
        attr_name = attribute.get('name')
        if attr_name not in attr_name_id:
            raise ValueError(
                'Unknown attribute name: %r' % (attr_name,))
        attr_value = attribute.get('value')
        attr_ids[attr_name_id.get(
            attr_name)] = value_name_id.get(attr_value)
    return attr_ids
