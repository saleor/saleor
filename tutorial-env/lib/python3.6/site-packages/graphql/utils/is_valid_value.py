"""
    Implementation of isValidJSValue from graphql.s
"""

import collections
import json

from six import string_types

from ..type import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLScalarType,
)

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, List

_empty_list = []  # type: List


def is_valid_value(value, type):
    # type: (Any, Any) -> List
    """Given a type and any value, return True if that value is valid."""
    if isinstance(type, GraphQLNonNull):
        of_type = type.of_type
        if value is None:
            return [u'Expected "{}", found null.'.format(type)]

        return is_valid_value(value, of_type)

    if value is None:
        return _empty_list

    if isinstance(type, GraphQLList):
        item_type = type.of_type
        if not isinstance(value, string_types) and isinstance(
            value, collections.Iterable
        ):
            errors = []
            for i, item in enumerate(value):
                item_errors = is_valid_value(item, item_type)
                for error in item_errors:
                    errors.append(u"In element #{}: {}".format(i, error))

            return errors

        else:
            return is_valid_value(value, item_type)

    if isinstance(type, GraphQLInputObjectType):
        if not isinstance(value, collections.Mapping):
            return [u'Expected "{}", found not an object.'.format(type)]

        fields = type.fields
        errors = []

        for provided_field in sorted(value.keys()):
            if provided_field not in fields:
                errors.append(u'In field "{}": Unknown field.'.format(provided_field))

        for field_name, field in fields.items():
            subfield_errors = is_valid_value(value.get(field_name), field.type)
            errors.extend(
                u'In field "{}": {}'.format(field_name, e) for e in subfield_errors
            )

        return errors

    assert isinstance(type, (GraphQLScalarType, GraphQLEnumType)), "Must be input type"

    # Scalar/Enum input checks to ensure the type can parse the value to
    # a non-null value.
    parse_result = type.parse_value(value)
    if parse_result is None:
        return [u'Expected type "{}", found {}.'.format(type, json.dumps(value))]

    return _empty_list
