import graphene
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils.text import slugify
from graphql_relay import from_global_id

from ..product.models import AttributeChoiceValue, ProductAttribute


def get_node(info, id, only_type=None):
    """Return node or throw an error if the node does not exist."""
    node = graphene.Node.get_node_from_global_id(info, id, only_type=only_type)
    if not node:
        raise Exception(
            "Could not resolve to a node with the global id of '%s'." % id)
    return node


def get_nodes(ids, graphene_type):
    """Return a list of nodes of proper type."""
    pks = []
    for graphql_id in ids:
        _type, _id = from_global_id(graphql_id)
        assert str(graphene_type) == _type, (
            'Must receive an {} id.').format(graphene_type._meta.name)
        pks.append(_id)
    nodes = list(graphene_type._meta.model.objects.filter(pk__in=pks))
    if not nodes:
        raise Exception(
            "Could not resolve to a nodes with the global id list of '%s'."
            % ids)
    nodes_pk_list = [str(node.pk) for node in nodes]
    for pk in pks:
        assert pk in nodes_pk_list, (
            'There is no node of type {} with pk {}'.format(_type, pk)
        )
    return nodes


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
        if not value:
            continue

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


def filter_by_query_param(queryset, query, search_fields):
    """Filter queryset according to given parameters.

    Keyword arguments:
    queryset - queryset to be filtered
    query - search string
    search_fields - fields considered in filtering
    """
    if query:
        query_by = {
            '{0}__{1}'.format(
                field, 'icontains'): query for field in search_fields}
        query_objects = Q()
        for q in query_by:
            query_objects |= Q(**{q:query_by[q]})
        return queryset.filter(query_objects)
    return queryset


def generate_query_argument_description(search_fields):
    header = 'Supported filter parameters:\n'
    supported_list = ''
    for field in search_fields:
        supported_list += '* {0}\n'.format(field)
    return header + supported_list
