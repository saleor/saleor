from functools import wraps
from json import JSONDecodeError

import graphene
from graphene.relay import Connection, is_node
from graphql import GraphQLError

from ...core.permissions import message_one_of_permissions_required
from ..decorators import one_of_permissions_required
from .connection import FILTERS_NAME, FILTERSET_CLASS


class PermissionsField(graphene.Field):
    def __init__(self, *args, **kwargs):
        self.permissions = kwargs.pop("permissions", [])
        auto_permission_message = kwargs.pop("auto_permission_message", True)
        assert isinstance(self.permissions, list), (
            "FieldWithPermissions `permissions` argument must be a list: "
            f"{self.permissions}"
        )

        super(PermissionsField, self).__init__(*args, **kwargs)
        if auto_permission_message and self.permissions:
            permissions_msg = message_one_of_permissions_required(self.permissions)
            description = self.description or ""
            self.description = description + permissions_msg

    def get_resolver(self, parent_resolver):
        resolver = self.resolver or parent_resolver
        if self.permissions:
            resolver = one_of_permissions_required(self.permissions)(resolver)
        return resolver


class ConnectionField(PermissionsField):
    def __init__(self, type_, *args, **kwargs):
        kwargs.setdefault(
            "before",
            graphene.String(
                description=(
                    "Return the elements in the list that come before "
                    "the specified cursor."
                )
            ),
        )
        kwargs.setdefault(
            "after",
            graphene.String(
                description=(
                    "Return the elements in the list that come after "
                    "the specified cursor."
                )
            ),
        )
        kwargs.setdefault(
            "first",
            graphene.Int(description="Return the first n elements from the list."),
        )
        kwargs.setdefault(
            "last",
            graphene.Int(description="Return the last n elements from the list."),
        )
        super().__init__(type_, *args, **kwargs)

    @property
    def type(self):
        type = super(ConnectionField, self).type
        connection_type = type
        if isinstance(type, graphene.NonNull):
            connection_type = type.of_type

        if is_node(connection_type):
            raise Exception(
                "ConnectionFields now need a explicit ConnectionType for Nodes.\n"
                "Read more: https://github.com/graphql-python/graphene/blob/v2.0.0/"
                "UPGRADE-v2.0.md#node-connections"
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


class JSONString(graphene.JSONString):
    @staticmethod
    def parse_literal(node):
        try:
            return graphene.JSONString.parse_literal(node)
        except JSONDecodeError:
            raise GraphQLError(f"{str(node.value)[:20]}... is not a valid JSONString")
