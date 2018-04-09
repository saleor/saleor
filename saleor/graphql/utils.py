import graphene
from django.utils.encoding import smart_text
from django.utils.text import slugify

from ..product.models import AttributeChoiceValue, ProductAttribute


def get_node(info, id, only_type=None):
    """Return node or throw an error if the node does not exist."""
    node = graphene.Node.get_node_from_global_id(info, id, only_type=only_type)
    if not node:
        raise Exception(
            "Could not resolve to a node with the global id of '%s'." % id)
    return node


def get_attributes_dict_from_list(attributes, attr_slug_id):
    """
    :param attributes: list
    :return: dict
    Takes list on form [{"slug": "attr_slug", "value": "attr_value"}, {...}]
    and converts into dictionary {attr_pk: value_pk}
    """
    attr_ids = {}
    value_slug_id = dict(
        AttributeChoiceValue.objects.values_list('name', 'id'))
    for attribute in attributes:
        attr_slug = attribute.get('slug')
        if attr_slug not in attr_slug_id:
            raise ValueError(
                'Unknown attribute slug: %r' % (attr_slug,))
        value = attribute.get('value')
        if value:
            if not value_slug_id.get(value):
                attr = ProductAttribute.objects.get(slug=attr_slug)
                value = AttributeChoiceValue(
                    attribute_id=attr.pk, name=value, slug=slugify(value))
                value.save()
                attr_ids[smart_text(
                    attr_slug_id.get(attr_slug))] = smart_text(value.pk)
            else:
                attr_ids[smart_text(attr_slug_id.get(attr_slug))] = smart_text(
                    value_slug_id.get(value))
    return attr_ids
