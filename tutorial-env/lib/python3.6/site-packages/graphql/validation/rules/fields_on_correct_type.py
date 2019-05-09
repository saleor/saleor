from collections import Counter

from ...error import GraphQLError
from ...pyutils.ordereddict import OrderedDict
from ...type.definition import GraphQLInterfaceType, GraphQLObjectType, GraphQLUnionType
from ...utils.quoted_or_list import quoted_or_list
from ...utils.suggestion_list import suggestion_list
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import Field, InlineFragment
    from typing import Any, List, Union

try:
    # Python 2
    from itertools import izip  # type: ignore
except ImportError:
    # Python 3
    izip = zip


def _undefined_field_message(field_name, type, suggested_types, suggested_fields):
    message = 'Cannot query field "{}" on type "{}".'.format(field_name, type)

    if suggested_types:
        suggestions = quoted_or_list(suggested_types)
        message += " Did you mean to use an inline fragment on {}?".format(suggestions)
    elif suggested_fields:
        suggestions = quoted_or_list(suggested_fields)
        message += " Did you mean {}?".format(suggestions)

    return message


class OrderedCounter(Counter, OrderedDict):
    pass


class FieldsOnCorrectType(ValidationRule):
    """Fields on correct type

      A GraphQL document is only valid if all fields selected are defined by the
      parent type, or are an allowed meta field such as __typenamme
    """

    def enter_Field(
        self,
        node,  # type: Field
        key,  # type: int
        parent,  # type: Union[List[Union[Field, InlineFragment]], List[Field]]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> None
        parent_type = self.context.get_parent_type()
        if not parent_type:
            return

        field_def = self.context.get_field_def()
        if not field_def:
            #  This field doesn't exist, lets look for suggestions.
            schema = self.context.get_schema()
            field_name = node.name.value

            # First determine if there are any suggested types to condition on.
            suggested_type_names = get_suggested_type_names(
                schema, parent_type, field_name
            )
            # if there are no suggested types perhaps it was a typo?
            suggested_field_names = (
                []
                if suggested_type_names
                else get_suggested_field_names(schema, parent_type, field_name)
            )

            # report an error including helpful suggestions.
            self.context.report_error(
                GraphQLError(
                    _undefined_field_message(
                        field_name,
                        parent_type.name,
                        suggested_type_names,
                        suggested_field_names,
                    ),
                    [node],
                )
            )


def get_suggested_type_names(schema, output_type, field_name):
    """Go through all of the implementations of type, as well as the interfaces
      that they implement. If any of those types include the provided field,
      suggest them, sorted by how often the type is referenced,  starting
      with Interfaces."""

    if isinstance(output_type, (GraphQLInterfaceType, GraphQLUnionType)):
        suggested_object_types = []
        interface_usage_count = OrderedDict()
        for possible_type in schema.get_possible_types(output_type):
            if not possible_type.fields.get(field_name):
                return

            # This object type defines this field.
            suggested_object_types.append(possible_type.name)

            for possible_interface in possible_type.interfaces:
                if not possible_interface.fields.get(field_name):
                    continue

                # This interface type defines this field.
                interface_usage_count[possible_interface.name] = (
                    interface_usage_count.get(possible_interface.name, 0) + 1
                )

        # Suggest interface types based on how common they are.
        suggested_interface_types = sorted(
            list(interface_usage_count.keys()),
            key=lambda k: interface_usage_count[k],
            reverse=True,
        )

        # Suggest both interface and object types.
        suggested_interface_types.extend(suggested_object_types)
        return suggested_interface_types

    # Otherwise, must be an Object type, which does not have possible fields.
    return []


def get_suggested_field_names(schema, graphql_type, field_name):
    """For the field name provided, determine if there are any similar field names
    that may be the result of a typo."""

    if isinstance(graphql_type, (GraphQLInterfaceType, GraphQLObjectType)):
        possible_field_names = list(graphql_type.fields.keys())

        return suggestion_list(field_name, possible_field_names)

    # Otherwise, must be a Union type, which does not define fields.
    return []
