import graphene
from django.db.models import Q
from django.utils.encoding import smart_text
from django.utils.text import slugify
from graphene_django.registry import get_global_registry
from graphql_relay import from_global_id

from ..product.models import AttributeChoiceValue, ProductAttribute
from .core.types import PermissionDisplay

registry = get_global_registry()


def get_node(info, id, only_type=None):
    """Return node or throw an error if the node does not exist."""
    node = graphene.Node.get_node_from_global_id(info, id, only_type=only_type)
    if not node:
        raise Exception(
            "Could not resolve to a node with the global id of '%s'." % id)
    return node


def get_nodes(ids, graphene_type=None):
    """Return a list of nodes.

    If the `graphene_type` argument is provided, the IDs will be validated
    against this type. If the type was not provided, it will be looked up in
    the Graphene's registry. Raises an error if not all IDs are of the same
    type.
    """
    pks = []
    types = []
    for graphql_id in ids:
        _type, _id = from_global_id(graphql_id)
        if graphene_type:
            assert str(graphene_type) == _type, (
                'Must receive an {} id.').format(graphene_type._meta.name)
        pks.append(_id)
        types.append(_type)

    # If `graphene_type` was not provided, check if all resolved types are
    # the same. This prevents from accidentally mismatching IDs of different
    # types.
    if types and not graphene_type:
        assert len(set(types)) == 1, 'Received IDs of more than one type.'
        # get type by name
        type_name = types[0]
        for model, _type in registry._registry.items():
            if _type._meta.name == type_name:
                graphene_type = _type
                break

    nodes = list(graphene_type._meta.model.objects.filter(pk__in=pks))
    if not nodes:
        raise Exception(
            "Could not resolve to a nodes with the global id list of '%s'."
            % ids)
    nodes_pk_list = [str(node.pk) for node in nodes]
    for pk in pks:
        assert pk in nodes_pk_list, (
            'There is no node of type {} with pk {}'.format(_type, pk))
    return nodes


def get_attributes_dict_from_list(attributes, slug_to_id_map):
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
        if attr_slug not in slug_to_id_map:
            raise ValueError(
                'Attribute %r doesn\'t belong to given product type.' % (
                    attr_slug,))
        value = attribute.get('value')
        if not value:
            continue

        if not value_slug_id.get(value):
            attr = ProductAttribute.objects.get(slug=attr_slug)
            value = AttributeChoiceValue(
                attribute_id=attr.pk, name=value, slug=slugify(value))
            value.save()
            attr_ids[smart_text(
                slug_to_id_map.get(attr_slug))] = smart_text(value.pk)
        else:
            attr_ids[smart_text(slug_to_id_map.get(attr_slug))] = smart_text(
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
            query_objects |= Q(**{q: query_by[q]})
        return queryset.filter(query_objects)
    return queryset


def generate_query_argument_description(search_fields):
    header = 'Supported filter parameters:\n'
    supported_list = ''
    for field in search_fields:
        supported_list += '* {0}\n'.format(field)
    return header + supported_list


def format_permissions_for_display(permissions):
    """Transform permissions queryset into PermissionDisplay list.

    Keyword arguments:
    permissions - queryset with permissions
    """
    return [
        PermissionDisplay(
            code='.'.join(
                [permission.content_type.app_label, permission.codename]),
            name=permission.name) for permission in permissions]
