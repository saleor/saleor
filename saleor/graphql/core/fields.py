from functools import wraps

import graphene
from graphene.relay import Connection, is_node

from .connection import FILTERS_NAME, FILTERSET_CLASS


def patch_pagination_args(field: "ConnectionField"):
    """Add descriptions to pagination arguments in a connection field.

    By default Graphene's connection fields comes without description for pagination
    arguments. This functions patches those fields to add the descriptions.
    """
    field.args["first"].description = "Return the first n elements from the list."
    field.args["last"].description = "Return the last n elements from the list."
    field.args[
        "before"
    ].description = (
        "Return the elements in the list that come before the specified cursor."
    )
    field.args[
        "after"
    ].description = (
        "Return the elements in the list that come after the specified cursor."
    )


class ConnectionField(graphene.Field):
    def __init__(self, type_, *args, **kwargs):
        kwargs.setdefault("before", graphene.String())
        kwargs.setdefault("after", graphene.String())
        kwargs.setdefault("first", graphene.Int())
        kwargs.setdefault("last", graphene.Int())
        super().__init__(type_, *args, **kwargs)
        patch_pagination_args(self)

    @property
    def type(self):
        type = super(ConnectionField, self).type
        connection_type = type
        if isinstance(type, graphene.NonNull):
            connection_type = type.of_type

        if is_node(connection_type):
            raise Exception(
                "ConnectionFields now need a explicit ConnectionType for Nodes.\n"
                "Read more: https://github.com/graphql-python/graphene/blob/v2.0.0/UPGRADE-v2.0.md#node-connections"
            )

        assert issubclass(connection_type, Connection), (
            '{} type have to be a subclass of Connection. Received "{}".'
        ).format(self.__class__.__name__, connection_type)
        return type


class FilterConnectionField(ConnectionField):
    def __init__(self, type_, *args, **kwargs):
        self.filter_field_name = kwargs.pop("filter_field_name", "filter")
        self.filter_input = kwargs.get(self.filter_field_name)
        self.filterset_class = None
        if self.filter_input:
            self.filterset_class = self.filter_input.filterset_class
        super().__init__(type_, *args, **kwargs)

    def get_resolver(self, parent_resolver):
        wrapped_resolver = super().get_resolver(parent_resolver)

        @wraps(wrapped_resolver)
        def new_resolver(obj, info, **kwargs):
            kwargs[FILTERSET_CLASS] = self.filterset_class
            kwargs[FILTERS_NAME] = self.filter_field_name
            return wrapped_resolver(obj, info, **kwargs)

        return new_resolver
