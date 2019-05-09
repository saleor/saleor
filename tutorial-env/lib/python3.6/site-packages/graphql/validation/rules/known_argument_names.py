from ...error import GraphQLError
from ...language import ast
from ...utils.quoted_or_list import quoted_or_list
from ...utils.suggestion_list import suggestion_list
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import Argument
    from typing import Any, List, Union


def _unknown_arg_message(arg_name, field_name, type, suggested_args):
    message = 'Unknown argument "{}" on field "{}" of type "{}".'.format(
        arg_name, field_name, type
    )
    if suggested_args:
        message += " Did you mean {}?".format(quoted_or_list(suggested_args))

    return message


def _unknown_directive_arg_message(arg_name, directive_name, suggested_args):
    message = 'Unknown argument "{}" on directive "@{}".'.format(
        arg_name, directive_name
    )
    if suggested_args:
        message += " Did you mean {}?".format(quoted_or_list(suggested_args))

    return message


class KnownArgumentNames(ValidationRule):
    def enter_Argument(
        self,
        node,  # type: Argument
        key,  # type: int
        parent,  # type: List[Argument]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> None
        argument_of = ancestors[-1]

        if isinstance(argument_of, ast.Field):
            field_def = self.context.get_field_def()
            if not field_def:
                return

            field_arg_def = field_def.args.get(node.name.value)

            if not field_arg_def:
                parent_type = self.context.get_parent_type()
                assert parent_type
                self.context.report_error(
                    GraphQLError(
                        _unknown_arg_message(
                            node.name.value,
                            argument_of.name.value,
                            parent_type.name,
                            suggestion_list(
                                node.name.value,
                                (arg_name for arg_name in field_def.args.keys()),
                            ),
                        ),
                        [node],
                    )
                )

        elif isinstance(argument_of, ast.Directive):
            directive = self.context.get_directive()
            if not directive:
                return

            directive_arg_def = directive.args.get(node.name.value)

            if not directive_arg_def:
                self.context.report_error(
                    GraphQLError(
                        _unknown_directive_arg_message(
                            node.name.value,
                            directive.name,
                            suggestion_list(
                                node.name.value,
                                (arg_name for arg_name in directive.args.keys()),
                            ),
                        ),
                        [node],
                    )
                )
