from ...error import GraphQLError
from ...language.printer import print_ast
from ...utils.is_valid_literal_value import is_valid_literal_value
from .base import ValidationRule

# Necessary for static type checking
if False:  # flake8: noqa
    from ...language.ast import Argument
    from typing import Any, List, Union


class ArgumentsOfCorrectType(ValidationRule):
    def enter_Argument(
        self,
        node,  # type: Argument
        key,  # type: int
        parent,  # type: List[Argument]
        path,  # type: List[Union[int, str]]
        ancestors,  # type: List[Any]
    ):
        # type: (...) -> bool
        arg_def = self.context.get_argument()
        if arg_def:
            errors = is_valid_literal_value(arg_def.type, node.value)
            if errors:
                self.context.report_error(
                    GraphQLError(
                        self.bad_value_message(
                            node.name.value, arg_def.type, print_ast(node.value), errors
                        ),
                        [node.value],
                    )
                )
        return False

    @staticmethod
    def bad_value_message(arg_name, type, value, verbose_errors):
        message = (u"\n" + u"\n".join(verbose_errors)) if verbose_errors else ""
        return 'Argument "{}" has invalid value {}.{}'.format(arg_name, value, message)
