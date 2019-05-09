import six

from .filterset import custom_filterset_factory, setup_filterset


def get_filtering_args_from_filterset(filterset_class, type):
    """ Inspect a FilterSet and produce the arguments to pass to
        a Graphene Field. These arguments will be available to
        filter against in the GraphQL
    """
    from ..forms.converter import convert_form_field

    args = {}
    for name, filter_field in six.iteritems(filterset_class.base_filters):
        field_type = convert_form_field(filter_field.field).Argument()
        field_type.description = filter_field.label
        args[name] = field_type

    return args


def get_filterset_class(filterset_class, **meta):
    """Get the class to be used as the FilterSet"""
    if filterset_class:
        # If were given a FilterSet class, then set it up and
        # return it
        return setup_filterset(filterset_class)
    return custom_filterset_factory(**meta)
