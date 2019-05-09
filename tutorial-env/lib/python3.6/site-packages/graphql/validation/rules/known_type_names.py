from ...error import GraphQLError
from ...utils.quoted_or_list import quoted_or_list
from ...utils.suggestion_list import suggestion_list
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import NamedType
    from typing import Any


def _unknown_type_message(type, suggested_types):
    message = 'Unknown type "{}".'.format(type)
    if suggested_types:
        message += " Perhaps you meant {}?".format(quoted_or_list(suggested_types))

    return message


class KnownTypeNames(ValidationRule):
    def enter_ObjectTypeDefinition(self, node, *args):
        return False

    def enter_InterfaceTypeDefinition(self, node, *args):
        return False

    def enter_UnionTypeDefinition(self, node, *args):
        return False

    def enter_InputObjectTypeDefinition(self, node, *args):
        return False

    def enter_NamedType(self, node, *args):
        # type: (NamedType, *Any) -> None
        schema = self.context.get_schema()
        type_name = node.name.value
        type = schema.get_type(type_name)

        if not type:
            self.context.report_error(
                GraphQLError(
                    _unknown_type_message(
                        type_name,
                        suggestion_list(type_name, list(schema.get_type_map().keys())),
                    ),
                    [node],
                )
            )
